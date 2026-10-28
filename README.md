# Arquitectura de Microservicios - Tienda Virtual

## Introducción

Este proyecto implementa una arquitectura de microservicios para una tienda virtual, utilizando FastAPI y Python. La solución separa las funcionalidades en servicios independientes que se comunican mediante API REST, demostrando los principios de arquitectura de microservicios, tolerancia a fallos y escalabilidad.

## Objetivo General

Diseñar e implementar una solución básica basada en arquitectura de microservicios, aplicando principios de separación de responsabilidades, comunicación mediante API REST y procesamiento independiente de funcionalidades.

## Objetivos Específicos

- ✓ Identificar las características, ventajas y desafíos de la arquitectura de microservicios
- ✓ Diseñar una solución de software mediante la separación de funcionalidades en servicios independientes
- ✓ Implementar microservicios básicos utilizando Python y FastAPI
- ✓ Validar la comunicación entre servicios y documentar los resultados obtenidos

## Arquitectura del Sistema

### Diagrama de Arquitectura

```
                 USUARIO
                    |
                    v
             APLICACIÓN CLIENTE
                    |
          +---------+---------+
          |         |         |
          v         v         v
      SERVICIO  SERVICIO  SERVICIO
     PRODUCTOS  CLIENTES  PEDIDOS
      (8001)    (8002)    (8003)
          |         |         |
          v         v         v
       Catálogo  Usuarios   Órdenes
```

### Microservicios Implementados

#### 1. Servicio de Productos (Puerto 8001)
**Responsabilidad:** Administrar el catálogo de productos

**Operaciones:**
- `GET /products` - Consultar todos los productos
- `GET /products/{id}` - Consultar un producto específico
- `POST /products` - Registrar un nuevo producto
- `PUT /products/{id}` - Modificar un producto
- `DELETE /products/{id}` - Eliminar un producto
- `GET /health` - Verificar estado del servicio

**Datos del producto:**
- id: int
- name: str
- description: str
- price: float
- stock: int

#### 2. Servicio de Clientes (Puerto 8002)
**Responsabilidad:** Administrar la información de clientes

**Operaciones:**
- `GET /customers` - Consultar todos los clientes
- `GET /customers/{id}` - Consultar un cliente específico
- `POST /customers` - Registrar un nuevo cliente
- `PUT /customers/{id}` - Modificar un cliente
- `DELETE /customers/{id}` - Eliminar un cliente
- `GET /health` - Verificar estado del servicio

**Datos del cliente:**
- id: int
- name: str
- email: str
- phone: str
- address: str

#### 3. Servicio de Pedidos (Puerto 8003)
**Responsabilidad:** Gestionar pedidos y coordinar con otros servicios

**Operaciones:**
- `GET /orders` - Consultar todos los pedidos
- `GET /orders/{id}` - Consultar un pedido específico
- `POST /orders` - Registrar un nuevo pedido
- `PUT /orders/{id}/status` - Actualizar estado de un pedido
- `GET /health` - Verificar estado del servicio

**Datos del pedido:**
- id: int
- customer_id: int
- items: List[OrderItem]
- total: float
- status: str
- created_at: str

**Dependencias:**
- Servicio de Productos: para validar productos y calcular precios
- Servicio de Clientes: para validar existencia del cliente

### Comunicación Entre Servicios

Los servicios se comunican mediante solicitudes HTTP usando el patrón REST:

1. **Pedidos → Productos:** El servicio de pedidos consulta información de productos para validar existencia y calcular el total
2. **Pedidos → Clientes:** El servicio de pedidos valida que el cliente exista antes de crear un pedido

**Tolerancia a Fallos:**
- Timeout de 3 segundos en llamadas entre servicios
- Manejo de excepciones con mensajes de error claros
- Los servicios independientes continúan funcionando aunque uno falle

## Instalación y Ejecución

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación de Dependencias

Cada servicio tiene su propio archivo `requirements.txt`:

```bash
# Servicio de Productos
cd products_service
pip install -r requirements.txt

# Servicio de Clientes
cd ../customers_service
pip install -r requirements.txt

# Servicio de Pedidos
cd ../orders_service
pip install -r requirements.txt
```

### Iniciar los Servicios

#### Opción 1: Automática (Windows)
```bash
start_services.bat
```

Este script:
- Instala las dependencias de cada servicio
- Inicia los tres servicios en ventanas separadas
- Servicio de Productos: http://localhost:8001
- Servicio de Clientes: http://localhost:8002
- Servicio de Pedidos: http://localhost:8003

#### Opción 2: Manual
En tres terminales separadas:

```bash
# Terminal 1 - Productos
cd products_service
python main.py

# Terminal 2 - Clientes
cd customers_service
python main.py

# Terminal 3 - Pedidos
cd orders_service
python main.py
```

### Pruebas del Sistema

#### Ejecutar pruebas completas:
```bash
python test_api.py
```

#### Ejecutar pruebas de tolerancia a fallos:
```bash
python test_fault_tolerance.py
```

## Análisis del Caso de la Tienda Virtual

### Problemas de la Arquitectura Monolítica Actual

1. **Dificultad de actualización:** No se puede actualizar el catálogo de productos sin afectar el registro de pedidos
2. **Escalabilidad limitada:** Durante temporadas de descuentos, el aumento de consultas de productos ralentiza toda la aplicación
3. **Acoplamiento funcional:** Todas las funcionalidades están en una sola aplicación, lo que dificulta el mantenimiento
4. **Punto único de fallo:** Si hay un error en una funcionalidad, puede afectar todo el sistema
5. **Despliegue complejo:** Cualquier cambio requiere desplegar toda la aplicación

### Funcionalidades Convertidas en Microservicios

1. **Servicio de Productos:** Gestión del catálogo de productos
2. **Servicio de Clientes:** Gestión de información de clientes
3. **Servicio de Pedidos:** Gestión de órdenes de compra

### Responsabilidades de Cada Servicio

| Servicio | Responsabilidad | Operaciones Principales |
|----------|----------------|------------------------|
| Productos | Administrar catálogo | Consultar, registrar, modificar, eliminar productos |
| Clientes | Administrar clientes | Registrar, consultar clientes |
| Pedidos | Gestionar pedidos | Registrar pedidos, consultar estado |

### Comunicación Entre Servicios

Los servicios se comunican mediante API REST:
- El servicio de Pedidos hace solicitudes HTTP a Productos y Clientes
- Se usan timeouts para manejar fallos de conexión
- Los errores se manejan con respuestas HTTP apropiadas (400, 404, 500)

### Ventajas de la Nueva Arquitectura

1. **Independencia de despliegue:** Cada servicio puede actualizarse por separado
2. **Escalabilidad granular:** Se puede escalar solo el servicio que necesita más recursos
3. **Tolerancia a fallos:** Si un servicio falla, los otros pueden continuar funcionando
4. **Tecnologías heterogéneas:** Cada servicio podría usar diferentes tecnologías si fuera necesario
5. **Mantenimiento simplificado:** Cada equipo puede trabajar en un servicio específico
6. **Desarrollo paralelo:** Múltiples equipos pueden trabajar en diferentes servicios simultáneamente

## Respuestas a Preguntas Orientadoras

### 1. ¿Cuál es la diferencia entre una arquitectura monolítica y una arquitectura de microservicios?

**Arquitectura Monolítica:**
- Todas las funcionalidades están en una sola aplicación
- Acoplamiento fuerte entre componentes
- Escalabilidad horizontal (escalar toda la aplicación)
- Despliegue unitario
- Un solo punto de fallo

**Arquitectura de Microservicios:**
- Funcionalidades separadas en servicios independientes
- Acoplamiento débil entre servicios
- Escalabilidad granular (escalar servicios específicos)
- Despliegue independiente
- Fallos aislados

### 2. ¿Por qué es importante que los microservicios tengan responsabilidades independientes?

- Permite que cada servicio evolucione independientemente
- Facilita la asignación de equipos especializados
- Reduce el acoplamiento y aumenta la cohesión
- Permite escalar solo lo necesario
- Mejora la comprensión del código (cada servicio es más simple)
- Facilita las pruebas unitarias

### 3. ¿Qué ventajas ofrece la comunicación mediante API REST?

- Estandarización y interoperabilidad
- Independencia de lenguaje y plataforma
- Uso de protocolos estándar (HTTP)
- Escalabilidad y cacheabilidad
- Simplicidad y facilidad de uso
- Soporte nativo en navegadores y herramientas
- Estado sin estado (stateless) facilita escalabilidad

### 4. ¿Qué sucede si uno de los microservicios deja de funcionar?

**En esta implementación:**
- Los servicios independientes continúan funcionando (Productos y Clientes pueden operar solos)
- El servicio de Pedidos maneja el fallo con errores controlados
- Los usuarios reciben mensajes de error claros
- El sistema no colapsa completamente

**En un sistema real:**
- Implementar patrones como Circuit Breaker
- Usar retries con backoff exponencial
- Implementar fallbacks alternativos
- Monitoreo y alertas automáticas
- Cacheo de datos críticos

### 5. ¿Cómo contribuyen los microservicios a la escalabilidad de una aplicación?

- **Escalabilidad horizontal individual:** Se puede agregar más instancias de un solo servicio
- **Escalabilidad vertical independiente:** Cada servicio puede tener recursos diferenciados
- **Load balancing:** Distribuir carga entre instancias del mismo servicio
- **Auto-scaling:** Escalar automáticamente según demanda
- **Optimización de recursos:** Asignar recursos según las necesidades de cada servicio

### 6. ¿Qué desafíos de seguridad y mantenimiento pueden presentarse al implementar esta arquitectura?

**Seguridad:**
- Autenticación y autorización distribuida
- Comunicación segura entre servicios (HTTPS, mTLS)
- Gestión de secrets y credenciales
- Validación de datos en cada servicio
- Rate limiting y prevención de abuso
- Auditoría y logging centralizado

**Mantenimiento:**
- Mayor complejidad operativa
- Gestión de múltiples repositorios
- Orquestación y despliegue (Docker, Kubernetes)
- Monitoreo distribuido
- Debugging más complejo
- Consistencia de datos entre servicios
- Versionado de APIs
- Pruebas de integración más complejas

## Evidencias de Ejecución

### Ejemplo de Uso

#### 1. Consultar productos
```bash
curl http://localhost:8001/products
```

#### 2. Consultar clientes
```bash
curl http://localhost:8002/customers
```

#### 3. Crear un pedido
```bash
curl -X POST http://localhost:8003/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "items": [
      {"product_id": 1, "quantity": 1},
      {"product_id": 2, "quantity": 2}
    ]
  }'
```

### Pruebas de Tolerancia a Fallos

El script `test_fault_tolerance.py` permite:
1. Verificar que los servicios funcionan independientemente
2. Simular el fallo de un servicio y verificar que los otros continúen funcionando
3. Validar el manejo de errores en dependencias

## Conclusiones Técnicas

### Logros Alcanzados

1. **Separación de responsabilidades:** Cada microservicio tiene una responsabilidad clara y bien definida
2. **Comunicación REST:** Los servicios se comunican eficientemente mediante API REST
3. **Independencia operativa:** Los servicios pueden iniciarse, detenerse y escalarse independientemente
4. **Tolerancia a fallos:** El sistema maneja fallos de servicios de manera controlada
5. **Escalabilidad:** La arquitectura permite escalar servicios individualmente según demanda

### Lecciones Aprendidas

1. La arquitectura de microservicios aumenta la complejidad operativa pero ofrece grandes beneficios en escalabilidad y mantenibilidad
2. Es crucial implementar mecanismos de tolerancia a fallos desde el diseño inicial
3. La comunicación entre servicios requiere timeouts y manejo de errores robusto
4. El monitoreo y logging son esenciales en sistemas distribuidos
5. La documentación clara de APIs es fundamental para el desarrollo

### Recomendaciones

1. Para un sistema en producción, implementar:
   - Autenticación centralizada (JWT, OAuth)
   - API Gateway para enrutamiento y seguridad
   - Message broker para comunicación asíncrona
   - Base de datos persistente para cada servicio
   - Orquestación con contenedores (Docker, Kubernetes)
   - Sistema de monitoreo y alertas
   - Circuit Breaker pattern para resiliencia

2. Considerar patrones avanzados:
   - Saga pattern para transacciones distribuidas
   - Event-driven architecture para desacoplamiento
   - Service mesh para comunicación segura
   - Distributed tracing para debugging

## Referencias Bibliográficas

1. Newman, S. (2015). *Building Microservices: Designing Fine-Grained Systems*. O'Reilly Media.
2. Richards, M., & Ford, N. (2016). *Microservices Patterns: With examples in Java*. Manning Publications.
3. Fowler, M. (2014). *Microservices*. Martin Fowler's Blog.
4. Fielding, R. T. (2000). *Architectural Styles and the Design of Network-based Software Architectures*. PhD Dissertation.
5. FastAPI Documentation: https://fastapi.tiangolo.com/

## Estructura del Proyecto

```
TALLER 4 - Arquitectura de Microservicios/
├── products_service/
│   ├── main.py              # Implementación del servicio de productos
│   └── requirements.txt     # Dependencias del servicio
├── customers_service/
│   ├── main.py              # Implementación del servicio de clientes
│   └── requirements.txt     # Dependencias del servicio
├── orders_service/
│   ├── main.py              # Implementación del servicio de pedidos
│   └── requirements.txt     # Dependencias del servicio
├── tests/                   # Directorio para pruebas adicionales
├── start_services.bat      # Script para iniciar todos los servicios (Windows)
├── test_api.py             # Script de pruebas integrales
├── test_fault_tolerance.py # Script de pruebas de tolerancia a fallos
└── README.md              # Esta documentación
```

## Autores

- Estudiante: [Nombre del estudiante]
- Asignatura: Arquitectura de Software / Sistemas Distribuidos
- Docente: [Nombre del docente]
- Fecha: Octubre 2026

## Licencia

Este proyecto es un entregable académico para la asignatura de Arquitectura de Software / Sistemas Distribuidos.
