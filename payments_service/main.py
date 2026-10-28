"""Microservicio de Pagos.

Administra pagos en memoria y valida por HTTP que el pedido asociado exista.
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


ORDERS_URL = os.getenv("ORDERS_SERVICE_URL", "http://localhost:8003").rstrip("/")
DEPENDENCY_TIMEOUT = float(os.getenv("DEPENDENCY_TIMEOUT_SECONDS", "2.0"))

app = FastAPI(
    title="Microservicio de Pagos",
    description="Registra pagos y valida pedidos mediante comunicación HTTP.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


PaymentMethod = Literal["card", "pse", "cash"]
PaymentStatus = Literal["pending", "approved", "rejected"]


class PaymentCreate(BaseModel):
    """Datos necesarios para registrar un pago."""

    id: Optional[int] = Field(default=None, gt=0)
    order_id: int = Field(gt=0)
    amount: Optional[float] = Field(default=None, gt=0)
    method: PaymentMethod = "card"


class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus


class Payment(BaseModel):
    id: int
    order_id: int
    amount: float
    method: PaymentMethod
    status: PaymentStatus
    created_at: str


class DependencyUnavailable(Exception):
    """Indica que Pedidos no respondió de forma utilizable."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


payments: list[Payment] = []
next_payment_id = count(start=1)


@app.get("/", tags=["Sistema"])
def home() -> dict[str, str]:
    return {"service": "payments", "status": "running"}


@app.get("/health", tags=["Sistema"])
def health() -> dict[str, str]:
    return {"service": "payments", "status": "healthy"}


async def get_order(order_id: int) -> Dict[str, Any]:
    """Consulta el pedido asociado con timeout y manejo de fallos."""
    try:
        timeout = httpx.Timeout(DEPENDENCY_TIMEOUT)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{ORDERS_URL}/orders/{order_id}")
        if response.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(status_code=400, detail="El pedido no existe")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("La respuesta no contiene un pedido válido")
        return payload
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        raise DependencyUnavailable("se agotó el tiempo de espera") from exc
    except httpx.RequestError as exc:
        raise DependencyUnavailable("no fue posible conectar con Pedidos") from exc
    except httpx.HTTPStatusError as exc:
        raise DependencyUnavailable(f"Pedidos respondió con HTTP {exc.response.status_code}") from exc
    except ValueError as exc:
        raise DependencyUnavailable("Pedidos respondió con JSON inválido") from exc


@app.get("/payments", response_model=list[Payment], tags=["Pagos"])
def list_payments() -> list[Payment]:
    return payments


@app.get("/payments/{payment_id}", response_model=Payment, tags=["Pagos"])
def get_payment(payment_id: int) -> Payment:
    for payment in payments:
        if payment.id == payment_id:
            return payment
    raise HTTPException(status_code=404, detail="El pago no existe")


@app.post(
    "/payments",
    response_model=Payment,
    status_code=status.HTTP_201_CREATED,
    tags=["Pagos"],
)
async def create_payment(data: PaymentCreate) -> Payment:
    """Registra un pago aprobado después de validar el pedido asociado."""
    if any(payment.order_id == data.order_id for payment in payments):
        raise HTTPException(status_code=409, detail="El pedido ya tiene un pago registrado")

    try:
        order = await get_order(data.order_id)
    except DependencyUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "DEPENDENCY_UNAVAILABLE",
                "message": "El pago no puede procesarse temporalmente porque Pedidos no está disponible.",
                "dependency": "Pedidos",
                "reason": exc.reason,
                "retryable": True,
            },
        ) from exc

    order_total = round(float(order["total"]), 2)
    if data.amount is not None and round(data.amount, 2) != order_total:
        raise HTTPException(
            status_code=409,
            detail=f"El monto debe coincidir con el total del pedido: {order_total}",
        )
    amount = order_total
    payment_id = data.id if data.id is not None else next(next_payment_id)
    if any(payment.id == payment_id for payment in payments):
        raise HTTPException(status_code=409, detail="Ya existe un pago con ese ID")

    payment = Payment(
        id=payment_id,
        order_id=data.order_id,
        amount=amount,
        method=data.method,
        status="approved",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    payments.append(payment)
    return payment


@app.patch("/payments/{payment_id}/status", response_model=Payment, tags=["Pagos"])
def update_payment_status(payment_id: int, data: PaymentStatusUpdate) -> Payment:
    for index, payment in enumerate(payments):
        if payment.id == payment_id:
            updated = payment.model_copy(update={"status": data.status})
            payments[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="El pago no existe")


@app.delete("/payments/{payment_id}", tags=["Pagos"])
def delete_payment(payment_id: int) -> Dict[str, Any]:
    for index, payment in enumerate(payments):
        if payment.id == payment_id:
            payments.pop(index)
            return {"message": "Pago eliminado correctamente", "id": payment_id}
    raise HTTPException(status_code=404, detail="El pago no existe")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
