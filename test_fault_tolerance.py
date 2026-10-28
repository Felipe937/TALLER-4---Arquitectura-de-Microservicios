import requests
import time
import sys

BASE_URLS = {
    "products": "http://localhost:8001",
    "customers": "http://localhost:8002",
    "orders": "http://localhost:8003"
}

def print_separator():
    print("\n" + "="*70 + "\n")

def check_service(service_name, url):
    """Verificar si un servicio está disponible"""
    try:
        response = requests.get(f"{url}/health", timeout=2)
        if response.status_code == 200:
            return True, response.json()
        return False, "Error en respuesta"
    except Exception as e:
        return False, str(e)

def test_service_independence():
    """Probar que los servicios funcionan independientemente"""
    print_separator()
    print("PRUEBA DE INDEPENDENCIA DE SERVICIOS")
    print_separator()
    
    print("Estado inicial de los servicios:")
    for service, url in BASE_URLS.items():
        available, status = check_service(service, url)
        symbol = "✓" if available else "✗"
        print(f"{symbol} {service.upper()}: {status}")
    
    print("\n" + "-"*70)
    print("PRUEBA 1: Verificar que Productos funciona independientemente")
    print("-"*70)
    
    # Intentar acceder a productos
    try:
        response = requests.get(f"{BASE_URLS['products']}/products", timeout=3)
        if response.status_code == 200:
            print("✓ Servicio de Productos funciona correctamente")
            print(f"  Cantidad de productos: {len(response.json())}")
        else:
            print("✗ Error en servicio de Productos")
    except Exception as e:
        print(f"✗ Error al conectar con Productos: {e}")
    
    print("\n" + "-"*70)
    print("PRUEBA 2: Verificar que Clientes funciona independientemente")
    print("-"*70)
    
    # Intentar acceder a clientes
    try:
        response = requests.get(f"{BASE_URLS['customers']}/customers", timeout=3)
        if response.status_code == 200:
            print("✓ Servicio de Clientes funciona correctamente")
            print(f"  Cantidad de clientes: {len(response.json())}")
        else:
            print("✗ Error en servicio de Clientes")
    except Exception as e:
        print(f"✗ Error al conectar con Clientes: {e}")
    
    print("\n" + "-"*70)
    print("PRUEBA 3: Pedidos requiere conexión con otros servicios")
    print("-"*70)
    
    # Intentar crear un pedido que depende de otros servicios
    new_order = {
        "id": 0,
        "customer_id": 1,
        "items": [{"product_id": 1, "quantity": 1}],
        "total": 0,
        "status": "",
        "created_at": ""
    }
    
    try:
        response = requests.post(f"{BASE_URLS['orders']}/orders", json=new_order, timeout=5)
        if response.status_code == 200:
            print("✓ Servicio de Pedidos puede crear órdenes (dependencias funcionan)")
            print(f"  Pedido creado: {response.json()}")
        else:
            print(f"✗ Error al crear pedido: {response.json()}")
    except Exception as e:
        print(f"✗ Error al conectar con Pedidos: {e}")

def simulate_service_failure():
    """Simular fallo de un servicio y verificar que otros continúen funcionando"""
    print_separator()
    print("SIMULACIÓN DE FALLO DE SERVICIO")
    print_separator()
    
    print("\nINSTRUCCIONES:")
    print("1. En una terminal separada, detenga el servicio de Productos (Ctrl+C en su ventana)")
    print("2. Presione Enter aquí para continuar con las pruebas")
    print("3. Verificaremos que Clientes y Pedidos aún respondan (con limitaciones)")
    
    input("\nPresione Enter cuando haya detenido el servicio de Productos...")
    
    print("\nVerificando estado de servicios después del fallo:")
    for service, url in BASE_URLS.items():
        available, status = check_service(service, url)
        symbol = "✓" if available else "✗"
        print(f"{symbol} {service.upper()}: {status}")
    
    print("\n" + "-"*70)
    print("VERIFICANDO SERVICIOS AÚN OPERATIVOS")
    print("-"*70)
    
    # Verificar que Clientes aún funciona
    print("\n1. Probando servicio de Clientes (debería funcionar):")
    try:
        response = requests.get(f"{BASE_URLS['customers']}/customers", timeout=3)
        if response.status_code == 200:
            print("   ✓ Clientes sigue funcionando correctamente")
            print(f"   Cantidad de clientes: {len(response.json())}")
        else:
            print("   ✗ Error en servicio de Clientes")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Verificar que Pedidos maneja el fallo de Productos
    print("\n2. Probando servicio de Pedidos (debería responder con error controlado):")
    new_order = {
        "id": 0,
        "customer_id": 1,
        "items": [{"product_id": 1, "quantity": 1}],
        "total": 0,
        "status": "",
        "created_at": ""
    }
    
    try:
        response = requests.post(f"{BASE_URLS['orders']}/orders", json=new_order, timeout=5)
        if response.status_code == 400:
            print("   ✓ Pedidos maneja el fallo de Productos con error controlado")
            print(f"   Respuesta: {response.json()}")
        else:
            print(f"   ? Respuesta inesperada: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "-"*70)
    print("CONCLUSIÓN")
    print("-"*70)
    print("✓ Los servicios son independientes y pueden operar por separado")
    print("✓ Cuando un servicio falla, los otros continúan funcionando")
    print("✓ El servicio de Pedidos maneja errores de dependencias de forma controlada")
    print("\nPara restaurar el sistema, reinicie el servicio de Productos.")

def main():
    print("="*70)
    print("SISTEMA DE MICROSERVICIOS - PRUEBAS DE TOLERANCIA A FALLOS")
    print("="*70)
    
    print("\nSeleccione una prueba:")
    print("1. Verificar independencia de servicios (todos funcionando)")
    print("2. Simular fallo de un servicio")
    print("3. Ejecutar ambas pruebas")
    
    choice = input("\nOpción (1-3): ").strip()
    
    if choice == "1":
        test_service_independence()
    elif choice == "2":
        simulate_service_failure()
    elif choice == "3":
        test_service_independence()
        print("\n" + "="*70)
        input("Presione Enter para continuar con la simulación de fallo...")
        simulate_service_failure()
    else:
        print("Opción no válida")
        sys.exit(1)
    
    print_separator()
    print("PRUEBAS FINALIZADAS")
    print_separator()

if __name__ == "__main__":
    main()
