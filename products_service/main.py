"""Microservicio de Productos.

El almacenamiento es una lista en memoria, tal como exige el taller.
"""

from __future__ import annotations

from itertools import count
from typing import Dict, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(
    title="Microservicio de Productos",
    description="Administra el catálogo de productos de la tienda virtual.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductCreate(BaseModel):
    """Datos necesarios para registrar un producto."""

    id: Optional[int] = Field(default=None, gt=0)
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(
        default="Producto registrado desde el dashboard",
        min_length=2,
        max_length=300,
    )
    price: float = Field(gt=0)
    stock: int = Field(default=100, ge=0)


class ProductUpdate(BaseModel):
    """Campos editables de un producto existente."""

    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=2, max_length=300)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)


class StockReservationItem(BaseModel):
    """Cantidad de un producto que se debe descontar del inventario."""

    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


class Product(ProductCreate):
    """Producto almacenado y expuesto por la API."""

    id: int


products: list[Product] = [
    Product(
        id=1,
        name="Laptop Lenovo IdeaPad",
        description="Laptop de 15 pulgadas con 8 GB de RAM y SSD de 512 GB.",
        price=2499000,
        stock=10,
    ),
    Product(
        id=2,
        name="Mouse inalámbrico",
        description="Mouse ergonómico inalámbrico de conexión USB.",
        price=79900,
        stock=25,
    ),
    Product(
        id=3,
        name="Teclado mecánico",
        description="Teclado mecánico con iluminación RGB.",
        price=189900,
        stock=15,
    ),
]
next_product_id = count(start=4)


@app.get("/", tags=["Sistema"])
def home() -> dict[str, str]:
    return {"service": "products", "status": "running"}


@app.get("/health", tags=["Sistema"])
def health() -> dict[str, str]:
    """Endpoint de salud para comprobar que el proceso está disponible."""
    return {"service": "products", "status": "healthy"}


@app.get("/products", response_model=list[Product], tags=["Productos"])
def list_products() -> list[Product]:
    """Consulta todos los productos del catálogo."""
    return products


@app.get("/products/{product_id}", response_model=Product, tags=["Productos"])
def get_product(product_id: int) -> Product:
    """Consulta un producto por su identificador."""
    for product in products:
        if product.id == product_id:
            return product
    raise HTTPException(status_code=404, detail="El producto no existe")


@app.post(
    "/products",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
)
def create_product(data: ProductCreate) -> Product:
    """Registra un producto y asigna su identificador en el servicio."""
    product_id = data.id if data.id is not None else next(next_product_id)
    if any(existing.id == product_id for existing in products):
        raise HTTPException(status_code=409, detail="Ya existe un producto con ese ID")
    product = Product(
        id=product_id,
        **data.model_dump(exclude={"id"}),
    )
    products.append(product)
    return product


@app.put("/products/{product_id}", response_model=Product, tags=["Productos"])
def update_product(product_id: int, data: ProductUpdate) -> Product:
    """Actualiza nombre, descripción, precio y stock de un producto."""
    for index, product in enumerate(products):
        if product.id == product_id:
            updated = Product(id=product_id, **data.model_dump())
            products[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="El producto no existe")


@app.delete("/products/{product_id}", tags=["Productos"])
def delete_product(product_id: int) -> Dict[str, Union[str, int]]:
    """Elimina un producto por su identificador."""
    for index, product in enumerate(products):
        if product.id == product_id:
            products.pop(index)
            return {"message": "Producto eliminado correctamente", "id": product_id}
    raise HTTPException(status_code=404, detail="El producto no existe")


@app.patch(
    "/products/stock",
    response_model=list[Product],
    tags=["Inventario"],
)
def decrease_stock(items: list[StockReservationItem]) -> list[Product]:
    """Descuenta inventario de forma validada para todos los artículos del pedido."""
    if not items:
        raise HTTPException(status_code=400, detail="El pedido no contiene productos")

    quantities: dict[int, int] = {}
    for item in items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity

    selected_products: dict[int, Product] = {}
    for product_id, quantity in quantities.items():
        product = next((item for item in products if item.id == product_id), None)
        if product is None:
            raise HTTPException(
                status_code=404,
                detail=f"El producto {product_id} no existe",
            )
        if product.stock < quantity:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Stock insuficiente para el producto {product_id}. "
                    f"Disponible: {product.stock}, solicitado: {quantity}"
                ),
            )
        selected_products[product_id] = product

    # Todas las cantidades se validan antes de modificar la lista: no queda
    # un pedido parcialmente descontado si uno de sus productos falla.
    for product_id, quantity in quantities.items():
        selected_products[product_id].stock -= quantity

    return list(selected_products.values())


@app.patch(
    "/products/stock/restore",
    response_model=list[Product],
    tags=["Inventario"],
)
def restore_stock(items: list[StockReservationItem]) -> list[Product]:
    """Devuelve al inventario las cantidades asociadas a un pedido eliminado."""
    if not items:
        raise HTTPException(status_code=400, detail="No hay cantidades para restaurar")

    quantities: dict[int, int] = {}
    for item in items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity

    selected_products: dict[int, Product] = {}
    for product_id in quantities:
        product = next((item for item in products if item.id == product_id), None)
        if product is None:
            raise HTTPException(
                status_code=404,
                detail=f"El producto {product_id} no existe",
            )
        selected_products[product_id] = product

    for product_id, quantity in quantities.items():
        selected_products[product_id].stock += quantity

    return list(selected_products.values())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
