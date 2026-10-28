from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Products Service", description="Microservicio para gestión de productos")

# Modelo de datos
class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int

# Base de datos en memoria
products_db = [
    Product(id=1, name="Laptop HP", description="Laptop de 15.6 pulgadas, 8GB RAM, 256GB SSD", price=899.99, stock=10),
    Product(id=2, name="Mouse Inalámbrico", description="Mouse ergonómico inalámbrico", price=29.99, stock=50),
    Product(id=3, name="Teclado Mecánico", description="Teclado mecánico RGB", price=79.99, stock=25),
    Product(id=4, name="Monitor 24 pulgadas", description="Monitor Full HD 1920x1080", price=199.99, stock=15),
    Product(id=5, name="Auriculares Bluetooth", description="Auriculares con cancelación de ruido", price=59.99, stock=30)
]
next_id = 6

@app.get("/")
def home():
    return {"service": "Products Service", "status": "running"}

@app.get("/products", response_model=List[Product])
def get_products():
    """Obtener todos los productos"""
    return products_db

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    """Obtener un producto por ID"""
    for product in products_db:
        if product.id == product_id:
            return product
    raise HTTPException(status_code=404, detail="Producto no encontrado")

@app.post("/products", response_model=Product)
def create_product(product: Product):
    """Crear un nuevo producto"""
    global next_id
    product.id = next_id
    next_id += 1
    products_db.append(product)
    return product

@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, product: Product):
    """Actualizar un producto"""
    for i, p in enumerate(products_db):
        if p.id == product_id:
            product.id = product_id
            products_db[i] = product
            return product
    raise HTTPException(status_code=404, detail="Producto no encontrado")

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    """Eliminar un producto"""
    for i, product in enumerate(products_db):
        if product.id == product_id:
            del products_db[i]
            return {"message": "Producto eliminado"}
    raise HTTPException(status_code=404, detail="Producto no encontrado")

@app.get("/health")
def health_check():
    """Verificar estado del servicio"""
    return {"status": "healthy", "service": "products"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
