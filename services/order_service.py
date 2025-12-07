"""OrderService with foreign key validation and business logic."""
from datetime import datetime
from sqlalchemy.orm import Session

from repositories.order_repository import OrderRepository
from repositories.client_repository import ClientRepository
from repositories.bill_repository import BillRepository
from repositories.base_repository_impl import InstanceNotFoundError
from schemas.order_schema import OrderSchema, OrderItemInput
from services.base_service_impl import BaseServiceImpl
from utils.logging_utils import get_sanitized_logger
from models.bill import BillModel
from models.enums import PaymentType
from models.order import OrderModel
from models.order_detail import OrderDetailModel
from models.product import ProductModel
from services.cache_service import cache_service

logger = get_sanitized_logger(__name__)


class OrderService(BaseServiceImpl):
    """Service for Order entity with validation and business logic."""

    def __init__(self, db: Session):
        super().__init__(
            repository_class=OrderRepository,
            model=OrderModel,
            schema=OrderSchema,
            db=db
        )
        self._client_repository = ClientRepository(db)
        self._bill_repository = BillRepository(db)
        self._db = db
        self._session = db

    def _generate_next_order_number(self) -> int:
        """
        Generate the next sequential order/bill number starting at 1000.

        Returns:
            int: Next order number
        """
        max_val = 999
        try:
            max_order = (
                self._session.query(OrderModel.id_key)
                .order_by(OrderModel.id_key.desc())
                .limit(1)
                .scalar()
            )
            if max_order and max_order > max_val:
                max_val = max_order

            rows = self._session.query(BillModel.bill_number).all()
            for (bn,) in rows:
                try:
                    num = int(bn)
                    if num > max_val:
                        max_val = num
                except (ValueError, TypeError):
                    continue
        except Exception as e:
            logger.warning(f"Could not compute next order number, defaulting to 1000. Reason: {e}")
        return max_val + 1

    def save(self, schema: OrderSchema) -> OrderSchema:
        """
        Create a new order with validation and generate a matching bill number.

        Order ID and bill number share the same counter (starting at 1000) so they stay in sync.
        """
        # Validate client exists
        try:
            self._client_repository.find(schema.client_id)
        except InstanceNotFoundError:
            logger.error(f"Client with id {schema.client_id} not found")
            raise InstanceNotFoundError(f"Client with id {schema.client_id} not found")

        items: list[OrderItemInput] = schema.items or []
        subtotal = 0.0

        # Validate stock and compute subtotal
        product_cache = {}
        for item in items:
            product = self._session.get(ProductModel, item.product_id)
            if product is None:
                raise InstanceNotFoundError(f"Product with id {item.product_id} not found")
            if product.stock is None or product.stock < item.quantity:
                raise ValueError(
                    f"No hay stock suficiente para el producto {product.id_key or product.id}. "
                    f"Disponible: {product.stock}, solicitado: {item.quantity}."
                )
            product_cache[item.product_id] = product
            price = product.price or 0
            subtotal += price * item.quantity

        # Apply discount and shipping (0)
        discount_pct = schema.discount_pct or 0
        discount_amount = subtotal * discount_pct / 100 if discount_pct > 0 else 0
        total = max(subtotal - discount_amount, 0)
        schema.total = total
        schema.date = schema.date or datetime.utcnow()

        # Shared counter for order id and bill number
        next_number = self._generate_next_order_number()

        try:
            # Update stock
            for item in items:
                product = product_cache[item.product_id]
                product.stock -= item.quantity
                if product.stock < 0:
                    raise ValueError(
                        f"No hay stock suficiente para el producto {product.id_key or product.id}. "
                        f"Disponible: {product.stock}, solicitado: {item.quantity}."
                    )
                self._session.add(product)

            # Create order with explicit id_key (sync with bill number)
            order_model = OrderModel(
                id_key=next_number,
                date=schema.date,
                total=total,
                delivery_method=schema.delivery_method,
                status=schema.status,
                client_id=schema.client_id,
            )
            self._session.add(order_model)
            self._session.flush()

            # Create or update bill so bill_number matches order id
            if schema.bill_id is None:
                bill_model = BillModel(
                    bill_number=str(next_number),
                    discount=discount_amount,
                    date=datetime.utcnow().date(),
                    total=total,
                    payment_type=PaymentType.CASH,
                    client_id=schema.client_id,
                )
                self._session.add(bill_model)
                self._session.flush()
                schema.bill_id = bill_model.id_key
                logger.info(f"Generated bill {bill_model.bill_number} for order (bill_id={schema.bill_id})")
            else:
                bill = self._session.get(BillModel, schema.bill_id)
                if bill is None:
                    logger.error(f"Bill with id {schema.bill_id} not found")
                    raise InstanceNotFoundError(f"Bill with id {schema.bill_id} not found")
                bill.bill_number = str(next_number)
                self._session.add(bill)
                self._session.flush()

            # Link order to bill
            order_model.bill_id = schema.bill_id
            self._session.add(order_model)

            # Create order details
            for item in items:
                product = product_cache[item.product_id]
                od = OrderDetailModel(
                    order_id=order_model.id_key,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=product.price,
                )
                self._session.add(od)

            self._session.commit()
            logger.info(f"Order {order_model.id_key} created with {len(items)} items; stock actualizado.")
            # Invalidate product caches to reflect new stock
            try:
                cache_service.delete_pattern("products:*")
            except Exception as e:
                logger.warning(f"No se pudo invalidar la caché de productos: {e}")
            return OrderSchema.model_validate(order_model)
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error creating order with items: {e}")
            raise

    def to_model(self, schema: OrderSchema) -> OrderModel:
        """Ensure required fields (like date) are set before persisting."""
        date_value = schema.date or datetime.utcnow()
        return OrderModel(
            date=date_value,
            total=schema.total,
            delivery_method=schema.delivery_method,
            status=schema.status,
            client_id=schema.client_id,
            bill_id=schema.bill_id,
        )

    def update(self, id_key: int, schema: OrderSchema) -> OrderSchema:
        """
        Update an order with validation

        Args:
            id_key: Order ID
            schema: Updated order data

        Returns:
            Updated order

        Raises:
            InstanceNotFoundError: If order, client, or bill doesn't exist
        """
        # Validate client exists if being updated
        if schema.client_id is not None:
            try:
                self._client_repository.find(schema.client_id)
            except InstanceNotFoundError:
                logger.error(f"Client with id {schema.client_id} not found")
                raise InstanceNotFoundError(f"Client with id {schema.client_id} not found")

        # Validate bill exists if being updated
        if schema.bill_id is not None:
            try:
                self._bill_repository.find(schema.bill_id)
            except InstanceNotFoundError:
                logger.error(f"Bill with id {schema.bill_id} not found")
                raise InstanceNotFoundError(f"Bill with id {schema.bill_id} not found")

        logger.info(f"Updating order {id_key}")
        return super().update(id_key, schema)
