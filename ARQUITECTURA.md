# Diagrama de Arquitectura de Microservicios

## Representación Visual

```
┌─────────────────────────────────────────────────────────────────┐
│                        USUARIO FINAL                             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APLICACIÓN CLIENTE                           │
│                   (Web / Móvil / API)                           │
└──────────────┬────────────────────────────┬─────────────────────┘
               │                            │
               ▼                            ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   SERVICIO DE PRODUCTOS  │  │   SERVICIO DE CLIENTES   │
│         (Port 8001)      │  │         (Port 8002)      │
├──────────────────────────┤  ├──────────────────────────┤
│ - GET /products          │  │ - GET /customers         │
│ - GET /products/{id}     │  │ - GET /customers/{id}    │
│ - POST /products         │  │ - POST /customers        │
│ - PUT /products/{id}     │  │ - PUT /customers/{id}    │
│ - DELETE /products/{id}  │  │ - DELETE /customers/{id} │
│ - GET /health            │  │ - GET /health            │
└───────────┬──────────────┘  └───────────┬──────────────┘
            │                             │
            └──────────────┬──────────────┘
                           ▼
               ┌──────────────────────────┐
               │   SERVICIO DE PEDIDOS     │
               │         (Port 8003)       │
               ├──────────────────────────┤
               │ - GET /orders            │
               │ - GET /orders/{id}       │
               │ - POST /orders           │◄─── Depende de Productos
               │ - PUT /orders/{id}/status│     y Clientes
               │ - GET /health            │
               └──────────────────────────┘
```

## Flujo de Datos

### Creación de un Pedido

```
Cliente → API Gateway → Servicio de Pedidos
                              │
                              ├─→ Servicio de Clientes (validar cliente)
                              │      │
                              │      └─→ Cliente existe ✓
                              │
                              └─→ Servicio de Productos (validar productos)
                                     │
                                     └─→ Productos existen ✓
                                           
                              └─→ Calcular total
                              └─→ Crear pedido
                              └─→ Respuesta al cliente
```

## Escenarios de Fallo

### Escenario 1: Servicio de Productos falla

```
Cliente → Servicio de Productos ✗ (No responde)
         ↓
    Servicio de Clientes ✓ (Sigue funcionando)
         ↓
    Servicio de Pedidos ✓ (Sigue funcionando, pero no puede crear pedidos que dependan de productos)
```

**Resultado:**
- ✓ Clientes pueden consultar su información
- ✓ Pedidos existentes pueden consultarse
- ✗ No se pueden crear nuevos pedidos (error controlado)
- ✓ El sistema no colapsa completamente

### Escenario 2: Servicio de Clientes falla

```
Cliente → Servicio de Clientes ✗ (No responde)
         ↓
    Servicio de Productos ✓ (Sigue funcionando)
         ↓
    Servicio de Pedidos ✓ (Sigue funcionando, pero no puede crear pedidos)
```

**Resultado:**
- ✓ Productos pueden consultarse
- ✓ Pedidos existentes pueden consultarse
- ✗ No se pueden crear nuevos pedidos (error controlado)
- ✓ El sistema no colapsa completamente

### Escenario 3: Servicio de Pedidos falla

```
Cliente → Servicio de Pedidos ✗ (No responde)
         ↓
    Servicio de Productos ✓ (Sigue funcionando)
         ↓
    Servicio de Clientes ✓ (Sigue funcionando)
```

**Resultado:**
- ✓ Productos pueden consultarse y gestionarse
- ✓ Clientes pueden consultarse y gestionarse
- ✗ No se pueden crear ni consultar pedidos
- ✓ El sistema no colapsa completamente

## Escalabilidad

### Escalado Vertical (más recursos)

```
Servicio de Productos: 2 CPU, 4GB RAM
Servicio de Clientes: 1 CPU, 2GB RAM
Servicio de Pedidos: 2 CPU, 4GB RAM
```

### Escalado Horizontal (más instancias)

```
            Load Balancer
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌────────┐    ┌────────┐    ┌────────┐
│Prod #1 │    │Prod #2 │    │Prod #3 │
└────────┘    └────────┘    └────────┘
```

## Puertos y Endpoints

| Servicio | Puerto | Endpoint Base |
|----------|--------|---------------|
| Productos | 8001 | http://localhost:8001 |
| Clientes | 8002 | http://localhost:8002 |
| Pedidos | 8003 | http://localhost:8003 |

## Dependencias de Servicios

```
┌─────────────────────────────────────────────┐
│               Servicios                      │
├─────────────────────────────────────────────┤
│ Productos   → Independiente                  │
│ Clientes    → Independiente                  │
│ Pedidos     → Depende de Productos + Clientes│
└─────────────────────────────────────────────┘
```

## Tecnologías Utilizadas

- **Lenguaje:** Python 3.8+
- **Framework Web:** FastAPI
- **Servidor ASGI:** Uvicorn
- **Cliente HTTP:** httpx (para comunicación entre servicios)
- **Protocolo:** HTTP/REST
- **Formato de datos:** JSON
