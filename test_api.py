import requests
import time
import json

BASE_URLS = {
    "products": "http://localhost:8001",
    "customers": "http://localhost:8002",
    "orders": "http://localhost:8003"
}

def print_separator():
    print("\n" + "="*60 + "\n")

def test_service_health():
    """Verificar estado de todos los servicios"""
    print_separator()
    print("VERIFICANDO SALUD DE LOS SERVICIOS")
    print_separator()
    
    for service, url in BASE_URLS.items():
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                print(f"✓ {service.upper()}: {response.json()}")
            else:
                print(f"✗ {service.upper()}: Error en respuesta")
        except Exception as e:
            print(f"✗ {service.upper()}: No disponible - {str(e)}")

def test_products_service():
    """Probar servicio de productos"""
    print_separator()
    print("PRUEBAS - SERVICIO DE PRODUCTOS")
    print_separator()
    
    # Obtener todos los productos
    response = requests.get(f"{BASE_URLS['products']}/products")
    print(f"GET /products - Status: {response.status_code}")
    print(f"Productos: {json.dumps(response.json(), indent=2)}")
    
    # Obtener un producto específico
    response = requests.get(f"{BASE_URLS['products']}/products/1")
    print(f"\nGET /products/1 - Status: {response.status_code}")
    print(f"Producto: {json.dumps(response.json(), indent=2)}")
    
    # Crear nuevo producto
    new_product = {
        "id": 0,
        "name": "Tablet Samsung",
        "description": "Tablet de 10 pulgadas, 64GB",
        "price": 299.99,
        "stock": 20
    }
    response = requests.post(f"{BASE_URLS['products']}/products", json=new_product)
    print(f"\nPOST /products - Status: {response.status_code}")
    print(f"Producto creado: {json.dumps(response.json(), indent=2)}")

def test_customers_service():
    """Probar servicio de clientes"""
    print_separator()
    print("PRUEBAS - SERVICIO DE CLIENTES")
    print_separator()
    
    # Obtener todos los clientes
    response = requests.get(f"{BASE_URLS['customers']}/customers")
    print(f"GET /customers - Status: {response.status_code}")
    print(f"Clientes: {json.dumps(response.json(), indent=2)}")
    
    # Obtener un cliente específico
    response = requests.get(f"{BASE_URLS['customers']}/customers/1")
    print(f"\nGET /customers/1 - Status: {response.status_code}")
    print(f"Cliente: {json.dumps(response.json(), indent=2)}")
    
    # Crear nuevo cliente
    new_customer = {
        "id": 0,
        "name": "Ana Martínez",
        "email": "ana.martinez@email.com",
        "phone": "+57 315 111 2222",
        "address": "Calle 10 #20-30, Barranquilla"
    }
    response = requests.post(f"{BASE_URLS['customers']}/customers", json=new_customer)
    print(f"\nPOST /customers - Status: {response.status_code}")
    print(f"Cliente creado: {json.dumps(response.json(), indent=2)}")

def test_orders_service():
    """Probar servicio de pedidos"""
    print_separator()
    print("PRUEBAS - SERVICIO DE PEDIDOS")
    print_separator()
    
    # Obtener todos los pedidos
    response = requests.get(f"{BASE_URLS['orders']}/orders")
    print(f"GET /orders - Status: {response.status_code}")
    print(f"Pedidos: {json.dumps(response.json(), indent=2)}")
    
    # Crear nuevo pedido
    new_order = {
        "id": 0,
        "customer_id": 1,
        "items": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 2}
        ],
        "total": 0,
        "status": "",
        "created_at": ""
    }
    response = requests.post(f"{BASE_URLS['orders']}/orders", json=new_order)
    print(f"\nPOST /orders - Status: {response.status_code}")
    print(f"Pedido creado: {json.dumps(response.json(), indent=2)}")
    
    # Obtener el pedido creado
    if response.status_code == 200:
        order_id = response.json()["id"]
        response = requests.get(f"{BASE_URLS['orders']}/orders/{order_id}")
        print(f"\nGET /orders/{order_id} - Status: {response.status_code}")
        print(f"Pedido: {json.dumps(response.json(), indent=2)}")

def test_fault_tolerance():
    """Probar tolerancia a fallos"""
    print_separator()
    print("PRUEBAS DE TOLERANCIA A FALLOS")
    print_separator()
    
    print("1. Intentando crear pedido con cliente inexistente...")
    invalid_order = {
        "id": 0,
        "customer_id": 999,
        "items": [{"product_id": 1, "quantity": 1}],
        "total": 0,
        "status": "",
        "created_at": ""
    }
    response = requests.post(f"{BASE_URLS['orders']}/orders", json=invalid_order)
    print(f"Status: {response.status_code}")
    print(f"Respuesta: {response.json()}")
    
    print("\n2. Intentando crear pedido con producto inexistente...")
    invalid_order2 = {
        "id": 0,
        "customer_id": 1,
        "items": [{"product_id": 999, "quantity": 1}],
        "total": 0,
        "status": "",
        "created_at": ""
    }
    response = requests.post(f"{BASE_URLS['orders']}/orders", json=invalid_order2)
    print(f"Status: {response.status_code}")
    print(f"Respuesta: {response.json()}")

def main():
    print("="*60)
    print("SISTEMA DE MICROSERVICIOS - TIENDA VIRTUAL")
    print("PRUEBAS INTEGRACIONALES")
    print("="*60)
    
    # Esperar a que los servicios inicien
    print("\nEsperando 5 segundos para que los servicios inicien...")
    time.sleep(5)
    
    try:
        test_service_health()
        test_products_service()
        test_customers_service()
        test_orders_service()
        test_fault_tolerance()
        
        print_separator()
        print("PRUEBAS COMPLETADAS")
        print_separator()
        
    except Exception as e:
        print(f"\nError durante las pruebas: {str(e)}")
        print("Asegúrese de que todos los servicios estén iniciados.")

if __name__ == "__main__":
    main()
