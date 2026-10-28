from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="Customers Service", description="Microservicio para gestión de clientes")

# Modelo de datos
class Customer(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    address: str

# Base de datos en memoria
customers_db = [
    Customer(id=1, name="Juan Pérez", email="juan.perez@email.com", phone="+57 300 123 4567", address="Calle 123 #45-67, Bogotá"),
    Customer(id=2, name="María García", email="maria.garcia@email.com", phone="+57 310 987 6543", address="Avenida 45 #67-89, Medellín"),
    Customer(id=3, name="Carlos Rodríguez", email="carlos.rodriguez@email.com", phone="+57 320 456 7890", address="Carrera 78 #90-12, Cali")
]
next_id = 4

@app.get("/")
def home():
    return {"service": "Customers Service", "status": "running"}

@app.get("/customers", response_model=List[Customer])
def get_customers():
    """Obtener todos los clientes"""
    return customers_db

@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int):
    """Obtener un cliente por ID"""
    for customer in customers_db:
        if customer.id == customer_id:
            return customer
    raise HTTPException(status_code=404, detail="Cliente no encontrado")

@app.post("/customers", response_model=Customer)
def create_customer(customer: Customer):
    """Crear un nuevo cliente"""
    global next_id
    customer.id = next_id
    next_id += 1
    customers_db.append(customer)
    return customer

@app.put("/customers/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, customer: Customer):
    """Actualizar un cliente"""
    for i, c in enumerate(customers_db):
        if c.id == customer_id:
            customer.id = customer_id
            customers_db[i] = customer
            return customer
    raise HTTPException(status_code=404, detail="Cliente no encontrado")

@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int):
    """Eliminar un cliente"""
    for i, customer in enumerate(customers_db):
        if customer.id == customer_id:
            del customers_db[i]
            return {"message": "Cliente eliminado"}
    raise HTTPException(status_code=404, detail="Cliente no encontrado")

@app.get("/health")
def health_check():
    """Verificar estado del servicio"""
    return {"status": "healthy", "service": "customers"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
