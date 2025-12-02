from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from config.database import get_db
from schemas.product_schema import ProductSchema, ProductCreate
from services.product_service import ProductService

class ProductController:
    def __init__(self):
        self.router = APIRouter(tags=["Products"])
        self._register_routes()

    def _register_routes(self):
        @self.router.get("/", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
        async def get_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
            return ProductService(db).get_all(skip=skip, limit=limit)

        @self.router.get("/{id_key}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
        async def get_one(id_key: int, db: Session = Depends(get_db)):
            return ProductService(db).get_one(id_key)

        @self.router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
        async def create(payload: ProductCreate, db: Session = Depends(get_db)):
            return ProductService(db).save(ProductSchema(**payload.model_dump()))

        # keep your update/delete as needed (copy from BaseControllerImpl or add similarly)
