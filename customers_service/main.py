"""Microservicio de Clientes.

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
    title="Microservicio de Clientes",
    description="Administra los clientes de la tienda virtual.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CustomerCreate(BaseModel):
    """Datos necesarios para registrar un cliente."""

    id: Optional[int] = Field(default=None, gt=0)
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str = Field(default="No registrado", min_length=3, max_length=30)
    address: str = Field(default="No registrada", min_length=3, max_length=200)


class CustomerUpdate(BaseModel):
    """Campos editables de un cliente existente."""

    name: str = Field(min_length=2, max_length=100)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str = Field(default="No registrado", min_length=3, max_length=30)
    address: str = Field(default="No registrada", min_length=3, max_length=200)


class Customer(CustomerCreate):
    id: int


customers: list[Customer] = [
    Customer(
        id=1,
        name="Ana Martínez",
        email="ana.martinez@example.com",
        phone="+57 300 123 4567",
        address="Calle 10 #20-30, Bogotá",
    ),
    Customer(
        id=2,
        name="Carlos Rodríguez",
        email="carlos.rodriguez@example.com",
        phone="+57 310 987 6543",
        address="Carrera 45 #67-89, Medellín",
    ),
]
next_customer_id = count(start=3)


@app.get("/", tags=["Sistema"])
def home() -> dict[str, str]:
    return {"service": "customers", "status": "running"}


@app.get("/health", tags=["Sistema"])
def health() -> dict[str, str]:
    """Endpoint de salud para comprobar que el proceso está disponible."""
    return {"service": "customers", "status": "healthy"}


@app.get("/customers", response_model=list[Customer], tags=["Clientes"])
def list_customers() -> list[Customer]:
    """Consulta todos los clientes registrados."""
    return customers


@app.get("/customers/{customer_id}", response_model=Customer, tags=["Clientes"])
def get_customer(customer_id: int) -> Customer:
    """Consulta un cliente por su identificador."""
    for customer in customers:
        if customer.id == customer_id:
            return customer
    raise HTTPException(status_code=404, detail="El cliente no existe")


@app.post(
    "/customers",
    response_model=Customer,
    status_code=status.HTTP_201_CREATED,
    tags=["Clientes"],
)
def create_customer(data: CustomerCreate) -> Customer:
    """Registra un cliente y asigna su identificador en el servicio."""
    customer_id = data.id if data.id is not None else next(next_customer_id)
    if any(existing.id == customer_id for existing in customers):
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese ID")
    customer = Customer(
        id=customer_id,
        **data.model_dump(exclude={"id"}),
    )
    customers.append(customer)
    return customer


@app.put("/customers/{customer_id}", response_model=Customer, tags=["Clientes"])
def update_customer(customer_id: int, data: CustomerUpdate) -> Customer:
    """Actualiza los datos de un cliente existente."""
    for index, customer in enumerate(customers):
        if customer.id == customer_id:
            updated = Customer(id=customer_id, **data.model_dump())
            customers[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="El cliente no existe")


@app.delete("/customers/{customer_id}", tags=["Clientes"])
def delete_customer(customer_id: int) -> Dict[str, Union[str, int]]:
    """Elimina un cliente por su identificador."""
    for index, customer in enumerate(customers):
        if customer.id == customer_id:
            customers.pop(index)
            return {"message": "Cliente eliminado correctamente", "id": customer_id}
    raise HTTPException(status_code=404, detail="El cliente no existe")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
