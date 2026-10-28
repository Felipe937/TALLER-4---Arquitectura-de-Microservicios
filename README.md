# Taller de Arquitectura de Microservicios: Tienda Virtual

Solución completa del taller universitario: microservicios en Python y
FastAPI para Productos, Clientes, Pedidos y Pagos, comunicación HTTP entre
servicios, manejo de fallos y documento teórico final.

## Estructura

```text
.
├── products_service/
│   └── main.py
├── customers_service/
│   └── main.py
├── orders_service/
│   └── main.py
├── payments_service/
│   └── main.py
├── requirements.txt
├── test_fault_tolerance.py
├── DOCUMENTO_FINAL.md
└── README.md
```

## Responsabilidades

| Servicio | Puerto | Operaciones |
|---|---:|---|
| Productos | 8001 | Registrar, consultar, actualizar, eliminar y descontar stock |
| Clientes | 8002 | Registrar, consultar, actualizar y eliminar clientes |
| Pedidos | 8003 | Registrar, consultar, actualizar estado y eliminar pedidos |
| Pagos | 8004 | Validar pedidos y registrar pagos |

Los tres servicios usan listas en memoria. No se utiliza una base de datos
externa.

FastAPI genera documentación OpenAPI automáticamente:

- Productos: <http://localhost:8001/docs>
- Clientes: <http://localhost:8002/docs>
- Pedidos: <http://localhost:8003/docs>
- Pagos: <http://localhost:8004/docs>

## Instalación

Se recomienda Python 3.11 o superior.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

## Ejecución

Abra cuatro terminales desde la raíz del proyecto:

```powershell
py products_service/main.py
```

```powershell
py customers_service/main.py
```

```powershell
py orders_service/main.py
```

```powershell
py payments_service/main.py
```

También se pueden configurar las URLs de dependencias de Pedidos mediante
variables de entorno:

```powershell
$env:PRODUCTS_SERVICE_URL = "http://localhost:8001"
$env:CUSTOMERS_SERVICE_URL = "http://localhost:8002"
$env:DEPENDENCY_TIMEOUT_SECONDS = "2.0"
py orders_service/main.py
```

## Dashboard Web

El archivo `index.html` contiene una interfaz visual construida con HTML,
JavaScript y Tailwind CSS mediante CDN. Permite registrar clientes, consultar
el catálogo, crear productos, procesar pedidos y registrar pagos desde el
navegador.

La forma recomendada de iniciar todo el sistema en Windows es:

```powershell
.\start_services.bat
```

El script inicia los tres microservicios y un servidor estático para el
dashboard. El navegador se abre en:

<http://localhost:5500/index.html>

Si los microservicios ya están ejecutándose, puede iniciar únicamente el
dashboard con:

```powershell
py -m http.server 5500
```

Luego visite <http://localhost:5500/index.html>. Cada columna comprueba su
propio servicio de forma independiente. Si un servicio no responde, muestra
`Servicio Inaccesible` en rojo sin bloquear los otros paneles. Los errores
devueltos por Pedidos, como cliente inexistente, producto inexistente o una
dependencia caída, se muestran en una alerta visual.

El dashboard utiliza `localStorage` para conservar clientes, productos y
pedidos que ya fueron consultados o registrados desde el navegador. Si un
servicio se desconecta, la interfaz muestra la última información disponible
localmente. Los clientes y productos creados mientras el servicio está caído
se sincronizan automáticamente cuando la API vuelve a estar disponible. Los
pedidos, en cambio, solo se guardan localmente después de que Pedidos confirma
su creación, porque deben validar las dependencias antes de considerarse
procesados.

## Ejemplos de uso

Consultar productos:

```powershell
curl http://localhost:8001/products
```

Registrar un cliente:

```powershell
curl -X POST http://localhost:8002/customers `
  -H "Content-Type: application/json" `
  -d '{"name":"Laura Gómez","email":"laura@example.com","phone":"+57 315 555 0000","address":"Calle 50 #10-20, Cali"}'
```

Crear un pedido:

```powershell
curl -X POST http://localhost:8003/orders `
  -H "Content-Type: application/json" `
  -d '{"customer_id":1,"items":[{"product_id":1,"quantity":1}]}'
```

Consultar el estado de un pedido:

```powershell
curl http://localhost:8003/orders/1
```

Actualizar el estado:

```powershell
curl -X PATCH "http://localhost:8003/orders/1/status?new_status=confirmed"
```

Registrar un pago asociado a un pedido:

```powershell
curl -X POST http://localhost:8004/payments `
  -H "Content-Type: application/json" `
  -d '{"order_id":1,"method":"card"}'
```

## Tolerancia a fallos

Pedidos usa `httpx.AsyncClient` con timeout configurable. Captura timeouts,
errores de conexión, respuestas HTTP no exitosas y JSON inválido. Cuando
Productos o Clientes no está disponible, responde `503` con un cuerpo similar
a este:

```json
{
  "detail": {
    "error": "DEPENDENCY_UNAVAILABLE",
    "message": "El pedido no puede crearse temporalmente porque un servicio dependiente no está disponible.",
    "dependency": "Productos",
    "reason": "se agotó el tiempo de espera",
    "retryable": true
  }
}
```

Las consultas de Clientes y las consultas de pedidos ya almacenados continúan
funcionando porque no dependen de Productos en tiempo de lectura.

## Prueba de tolerancia a fallos

Con los tres servicios activos, ejecute:

```powershell
py test_fault_tolerance.py
```

El script crea primero un pedido válido. Después solicita detener Productos y
presionar Enter. Verifica que Clientes siga respondiendo, que Pedidos pueda
consultar la orden existente y que un nuevo pedido falle de forma controlada
con HTTP `503`.

## Documento final

El contenido teórico completo, con portada, análisis, preguntas orientadoras,
diagrama explicado y conclusiones, está en
[DOCUMENTO_FINAL.md](DOCUMENTO_FINAL.md). Puede abrirse en cualquier editor
Markdown y exportarse a Word o PDF.
