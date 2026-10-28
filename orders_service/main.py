from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import httpx
from datetime import datetime

app = FastAPI(title="Orders Service", description="Microservicio para gestión de pedidos")

# URLs de otros microservicios
PRODUCTS_SERVICE_URL = "http://localhost:8001"
CUSTOMERS_SERVICE_URL = "http://localhost:8002"

# Modelo de datos
class OrderItem(BaseModel):
    product_id: int
    quantity: int

class Order(BaseModel):
    id: int
    customer_id: int
    items: List[OrderItem]
    total: float
    status: str
    created_at: str

# Base de datos en memoria
orders_db = []
next_id = 1

async def get_product(product_id: int):
    """Obtener información de un producto del servicio de productos"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{PRODUCTS_SERVICE_URL}/products/{product_id}")
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        print(f"Error al conectar con servicio de productos: {e}")
        return None

async def get_customer(customer_id: int):
    """Obtener información de un cliente del servicio de clientes"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{CUSTOMERS_SERVICE_URL}/customers/{customer_id}")
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        print(f"Error al conectar con servicio de clientes: {e}")
        return None

@app.get("/")
def home():
    return {"service": "Orders Service", "status": "running"}

@app.get("/orders", response_model=List[Order])
def get_orders():
    """Obtener todos los pedidos"""
    return orders_db

@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    """Obtener un pedido por ID"""
    for order in orders_db:
        if order.id == order_id:
            return order
    raise HTTPException(status_code=404, detail="Pedido no encontrado")

@app.post("/orders", response_model=Order)
async def create_order(order: Order):
    """Crear un nuevo pedido"""
    global next_id
    
    # Validar cliente (con tolerancia a fallos)
    customer = await get_customer(order.customer_id)
    if customer is None:
        raise HTTPException(
            status_code=400, 
            detail="Cliente no encontrado o servicio de clientes no disponible"
        )
    
    # Calcular total y validar productos (con tolerancia a fallos)
    total = 0.0
    items_validated = []
    
    for item in order.items:
        product = await get_product(item.product_id)
        if product is None:
            raise HTTPException(
                status_code=400,
                detail=f"Producto {item.product_id} no encontrado o servicio de productos no disponible"
            )
        total += product["price"] * item.quantity
        items_validated.append(item)
    
    # Crear pedido
    order.id = next_id
    next_id += 1
    order.total = total
    order.status = "pending"
    order.created_at = datetime.now().isoformat()
    order.items = items_validated
    
    orders_db.append(order)
    return order

@app.put("/orders/{order_id}/status")
def update_order_status(order_id: int, status: str):
    """Actualizar el estado de un pedido"""
    for order in orders_db:
        if order.id == order_id:
            order.status = status
            return order
    raise HTTPException(status_code=404, detail="Pedido no encontrado")

@app.get("/health")
def health_check():
    """Verificar estado del servicio"""
    return {"status": "healthy", "service": "orders"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
