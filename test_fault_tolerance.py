"""Prueba manual de integración y tolerancia a fallos.

Uso:
    1. Inicie los tres servicios.
    2. Ejecute: py test_fault_tolerance.py
    3. Cuando el script lo solicite, detenga Productos y pulse Enter.

El resultado esperado es que Clientes continúe respondiendo y que Pedidos
devuelva HTTP 503 de forma rápida y legible, sin finalizar el proceso.
"""

import argparse
import time

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prueba de tolerancia a fallos")
    parser.add_argument("--products-url", default="http://localhost:8001")
    parser.add_argument("--customers-url", default="http://localhost:8002")
    parser.add_argument("--orders-url", default="http://localhost:8003")
    return parser.parse_args()


def check_health(name: str, base_url: str) -> None:
    response = requests.get(f"{base_url}/health", timeout=3)
    if response.status_code != 200:
        raise AssertionError(f"{name} no está saludable: HTTP {response.status_code}")
    print(f"OK  {name}: {response.json()}")


def main() -> int:
    args = parse_args()
    services = {
        "Productos": args.products_url,
        "Clientes": args.customers_url,
        "Pedidos": args.orders_url,
    }

    print("1. Verificando disponibilidad inicial...")
    for name, url in services.items():
        check_health(name, url)

    print("\n2. Creando un pedido con todas las dependencias disponibles...")
    order_payload = {
        "customer_id": 1,
        "items": [{"product_id": 1, "quantity": 1}],
    }
    response = requests.post(
        f"{args.orders_url}/orders",
        json=order_payload,
        timeout=5,
    )
    if response.status_code != 201:
        raise AssertionError(f"No se pudo crear el pedido: {response.status_code} {response.text}")
    order_id = response.json()["id"]
    print(f"OK  Pedido creado con id={order_id}")

    print(
        "\n3. Detenga ahora el servicio de Productos en su terminal "
        "y pulse Enter para continuar."
    )
    input()

    print("\n4. Comprobando degradación controlada...")
    customer_response = requests.get(f"{args.customers_url}/customers/1", timeout=3)
    if customer_response.status_code != 200:
        raise AssertionError("Clientes dejó de responder cuando cayó Productos")
    print("OK  Clientes continúa disponible")

    existing_order_response = requests.get(
        f"{args.orders_url}/orders/{order_id}",
        timeout=3,
    )
    if existing_order_response.status_code != 200:
        raise AssertionError("Pedidos no pudo consultar un pedido existente")
    print("OK  Pedidos continúa consultando información local")

    started = time.perf_counter()
    failed_order_response = requests.post(
        f"{args.orders_url}/orders",
        json=order_payload,
        timeout=5,
    )
    elapsed = time.perf_counter() - started
    if failed_order_response.status_code != 503:
        raise AssertionError(
            "Pedidos no informó la caída de Productos como 503: "
            f"HTTP {failed_order_response.status_code}"
        )
    print(f"OK  Pedidos respondió 503 con degradación elegante en {elapsed:.2f}s")
    print(f"    Detalle: {failed_order_response.json()}")

    print("\nPrueba completada correctamente. Reinicie Productos al finalizar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
