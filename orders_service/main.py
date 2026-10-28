"""Microservicio de Pedidos.

Pedidos valida sus dependencias mediante HTTP. Los errores de red se
transforman en respuestas 503 claras para evitar que una caída externa rompa
el proceso completo.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from itertools import count
from typing import Any, Dict, Literal, Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


PRODUCTS_URL = os.getenv("PRODUCTS_SERVICE_URL", "http://localhost:8001").rstrip("/")
CUSTOMERS_URL = os.getenv("CUSTOMERS_SERVICE_URL", "http://localhost:8002").rstrip("/")
DEPENDENCY_TIMEOUT = float(os.getenv("DEPENDENCY_TIMEOUT_SECONDS", "2.0"))

app = FastAPI(
    title="Microservicio de Pedidos",
    description=(
        "Registra pedidos y valida productos y clientes mediante HTTP, "
        "con timeout y manejo explícito de fallos."
    ),
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


class OrderCreate(BaseModel):
    id: Optional[int] = Field(default=None, gt=0)
    customer_id: int = Field(gt=0)
    items: list[OrderItem] = Field(min_length=1, max_length=30)


OrderStatus = Literal["pending", "confirmed", "cancelled"]


class Order(BaseModel):
    id: int
    customer_id: int
    items: list[OrderItem]
    total: float
    status: OrderStatus
    created_at: str


class DependencyUnavailable(Exception):
    """Indica que una dependencia no respondió de forma utilizable."""

    def __init__(self, dependency: str, reason: str) -> None:
        self.dependency = dependency
        self.reason = reason
        super().__init__(f"{dependency}: {reason}")


orders: list[Order] = []
next_order_id = count(start=1)


async def get_dependency_resource(
    dependency: str,
    base_url: str,
    resource_path: str,
) -> Optional[Dict[str, Any]]:
    """Consulta un recurso con timeout y convierte fallos de red en una excepción propia."""
    try:
        timeout = httpx.Timeout(DEPENDENCY_TIMEOUT)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{base_url}{resource_path}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            return None

        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException as exc:
        raise DependencyUnavailable(dependency, "se agotó el tiempo de espera") from exc
    except httpx.RequestError as exc:
        raise DependencyUnavailable(dependency, "no fue posible establecer conexión") from exc
    except httpx.HTTPStatusError as exc:
        raise DependencyUnavailable(
            dependency,
            f"respondió con HTTP {exc.response.status_code}",
        ) from exc
    except ValueError as exc:
        raise DependencyUnavailable(dependency, "respondió con JSON inválido") from exc


async def decrease_product_stock(items: list[OrderItem]) -> None:
    """Solicita a Productos el descuento atómico del inventario del pedido."""
    try:
        timeout = httpx.Timeout(DEPENDENCY_TIMEOUT)
        payload = [item.model_dump() for item in items]
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.patch(f"{PRODUCTS_URL}/products/stock", json=payload)

        if response.status_code == status.HTTP_404_NOT_FOUND:
            detail = response.json().get("detail", "Producto no encontrado")
            raise HTTPException(status_code=400, detail=f"No se pudo descontar stock: {detail}")
        if response.status_code == status.HTTP_409_CONFLICT:
            detail = response.json().get("detail", "Stock insuficiente")
            raise HTTPException(status_code=409, detail=detail)

        response.raise_for_status()
        response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        raise DependencyUnavailable("Productos", "se agotó el tiempo de espera al actualizar stock") from exc
    except httpx.RequestError as exc:
        raise DependencyUnavailable("Productos", "no fue posible actualizar el stock") from exc
    except httpx.HTTPStatusError as exc:
        raise DependencyUnavailable(
            "Productos",
            f"respondió con HTTP {exc.response.status_code} al actualizar stock",
        ) from exc
    except ValueError as exc:
        raise DependencyUnavailable("Productos", "respondió con JSON inválido al actualizar stock") from exc


async def restore_product_stock(items: list[OrderItem]) -> None:
    """Devuelve al inventario las cantidades de un pedido eliminado."""
    try:
        timeout = httpx.Timeout(DEPENDENCY_TIMEOUT)
        payload = [item.model_dump() for item in items]
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.patch(
                f"{PRODUCTS_URL}/products/stock/restore",
                json=payload,
            )

        if response.status_code == status.HTTP_404_NOT_FOUND:
            detail = response.json().get("detail", "Producto no encontrado")
            raise HTTPException(status_code=400, detail=f"No se pudo restaurar stock: {detail}")

        response.raise_for_status()
        response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        raise DependencyUnavailable("Productos", "se agotó el tiempo de espera al restaurar stock") from exc
    except httpx.RequestError as exc:
        raise DependencyUnavailable("Productos", "no fue posible restaurar el stock") from exc
    except httpx.HTTPStatusError as exc:
        raise DependencyUnavailable(
            "Productos",
            f"respondió con HTTP {exc.response.status_code} al restaurar stock",
        ) from exc
    except ValueError as exc:
        raise DependencyUnavailable("Productos", "respondió con JSON inválido al restaurar stock") from exc


async def validate_order(data: OrderCreate) -> list[dict[str, Any]]:
    """Valida la existencia del cliente, productos y cantidades disponibles."""
    customer = await get_dependency_resource(
        "Clientes",
        CUSTOMERS_URL,
        f"/customers/{data.customer_id}",
    )
    if customer is None:
        raise HTTPException(
            status_code=400,
            detail=f"El cliente {data.customer_id} no existe en el servicio de Clientes",
        )

    product_data: list[dict[str, Any]] = []
    for item in data.items:
        product = await get_dependency_resource(
            "Productos",
            PRODUCTS_URL,
            f"/products/{item.product_id}",
        )
        if product is None:
            raise HTTPException(
                status_code=400,
                detail=f"El producto {item.product_id} no existe en el servicio de Productos",
            )
        if product["stock"] < item.quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Stock insuficiente para el producto {item.product_id}",
            )
        product_data.append(product)
    return product_data


@app.get("/", tags=["Sistema"])
def home() -> dict[str, str]:
    return {"service": "orders", "status": "running"}


@app.get("/health", tags=["Sistema"])
def health() -> dict[str, str]:
    """El health check no consulta dependencias: el servicio puede seguir atendiendo lecturas."""
    return {"service": "orders", "status": "healthy"}


@app.get("/orders", response_model=list[Order], tags=["Pedidos"])
def list_orders() -> list[Order]:
    """Consulta todos los pedidos almacenados en memoria."""
    return orders


@app.get("/orders/{order_id}", response_model=Order, tags=["Pedidos"])
def get_order(order_id: int) -> Order:
    """Consulta un pedido y su estado actual."""
    for order in orders:
        if order.id == order_id:
            return order
    raise HTTPException(status_code=404, detail="El pedido no existe")


@app.post(
    "/orders",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
    tags=["Pedidos"],
)
async def create_order(data: OrderCreate) -> Order:
    """Valida dependencias y registra un pedido."""
    order_id = data.id if data.id is not None else next(next_order_id)
    if any(existing.id == order_id for existing in orders):
        raise HTTPException(status_code=409, detail="Ya existe un pedido con ese ID")

    try:
        product_data = await validate_order(data)
        await decrease_product_stock(data.items)
    except DependencyUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "DEPENDENCY_UNAVAILABLE",
                "message": (
                    "El pedido no puede crearse temporalmente porque un servicio "
                    "dependiente no está disponible."
                ),
                "dependency": exc.dependency,
                "reason": exc.reason,
                "retryable": True,
            },
        ) from exc

    total = round(
        sum(product["price"] * item.quantity for product, item in zip(product_data, data.items)),
        2,
    )
    order = Order(
        id=order_id,
        customer_id=data.customer_id,
        items=data.items,
        total=total,
        status="pending",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    orders.append(order)
    return order


@app.delete("/orders/{order_id}", tags=["Pedidos"])
async def delete_order(order_id: int) -> dict[str, Any]:
    """Elimina un pedido y devuelve sus cantidades al inventario."""
    order = next((item for item in orders if item.id == order_id), None)
    if order is None:
        raise HTTPException(status_code=404, detail="El pedido no existe")

    try:
        await restore_product_stock(order.items)
    except DependencyUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "DEPENDENCY_UNAVAILABLE",
                "message": "El pedido no puede eliminarse temporalmente porque no se pudo restaurar el stock.",
                "dependency": exc.dependency,
                "reason": exc.reason,
                "retryable": True,
            },
        ) from exc

    orders.remove(order)
    return {"message": "Pedido eliminado correctamente", "id": order_id}


@app.patch("/orders/{order_id}/status", response_model=Order, tags=["Pedidos"])
def update_order_status(order_id: int, new_status: OrderStatus) -> Order:
    """Actualiza el estado de un pedido existente."""
    for index, order in enumerate(orders):
        if order.id == order_id:
            updated = order.model_copy(update={"status": new_status})
            orders[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="El pedido no existe")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
