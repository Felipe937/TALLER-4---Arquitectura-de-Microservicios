# Taller de Arquitectura de Microservicios

## 1. Portada

**Institución educativa:** ________________________________________________

**Facultad o programa:** _________________________________________________

**Asignatura:** Arquitectura de Software / Sistemas Distribuidos

**Título del trabajo:** Diseño e implementación de una arquitectura de
microservicios para una tienda virtual

**Estudiante:** __________________________________________________________

**Código:** ______________________________________________________________

**Docente:** _____________________________________________________________

**Ciudad:** ______________________________________________________________

**Fecha:** _______________________________________________________________

---

## 2. Introducción

La arquitectura de software define la forma en que se organizan los
componentes de un sistema, sus responsabilidades y los mecanismos mediante
los cuales se comunican. En una aplicación monolítica, las funcionalidades de
negocio se implementan dentro de una única unidad desplegable. Aunque este
enfoque puede ser adecuado para iniciar un proyecto pequeño, con el tiempo
puede producir un alto nivel de acoplamiento, dificultar la evolución
independiente de cada módulo y convertir un fallo local en una interrupción
general del sistema.

La arquitectura de microservicios propone dividir la aplicación en servicios
pequeños, autónomos y orientados a capacidades de negocio. Cada servicio tiene
una responsabilidad delimitada, puede ejecutarse y escalarse de forma
independiente, y expone una interfaz de comunicación claramente definida. La
separación no elimina la complejidad: la traslada desde el código interno de
una única aplicación hacia la comunicación, observabilidad, despliegue y
consistencia entre servicios. Por esta razón, una implementación adecuada
debe considerar desde el inicio los errores de red, los timeouts, la
validación de datos y las estrategias de degradación.

En este taller se diseña una solución para una tienda virtual mediante cuatro
microservicios desarrollados con Python y FastAPI: Productos, Clientes, Pedidos
y Pagos. Productos administra el catálogo; Clientes administra la información
de los compradores; Pedidos coordina la creación de órdenes validando por HTTP
la existencia del cliente y de los productos; y Pagos registra transacciones
asociadas a pedidos. Los datos se almacenan en
listas en memoria para concentrar el ejercicio en los principios de
arquitectura y comunicación distribuida.

El servicio de Pedidos incorpora manejo explícito de excepciones y timeouts.
Cuando Productos o Clientes no están disponibles, el sistema no expone una
excepción interna ni queda esperando indefinidamente. En su lugar, responde
con un mensaje controlado y el código HTTP `503 Service Unavailable`,
indicando que la operación puede reintentarse cuando la dependencia se
recupere.

## 3. Objetivos

### 3.1 Objetivo general

Diseñar e implementar una arquitectura de microservicios para una tienda
virtual utilizando Python, FastAPI y comunicación HTTP, aplicando separación
de responsabilidades, validación entre servicios y mecanismos básicos de
tolerancia a fallos.

### 3.2 Objetivos específicos

1. Identificar las limitaciones de una arquitectura monolítica aplicada al
   dominio de una tienda virtual.
2. Separar las capacidades de productos, clientes, pedidos y pagos en servicios
   independientes.
3. Implementar APIs REST documentadas automáticamente mediante OpenAPI y
   Swagger UI.
4. Almacenar temporalmente la información en listas en memoria, sin depender
   de bases de datos externas.
5. Validar desde Pedidos la existencia de clientes y productos mediante
   solicitudes HTTP.
6. Implementar timeouts y manejo de excepciones para evitar que la caída de
   una dependencia detenga todo el sistema.
7. Verificar mediante una prueba de integración que los servicios
   independientes continúan respondiendo ante una falla parcial.

## 4. Análisis del caso de la tienda virtual

### 4.1 ¿Cuáles son los principales problemas de la arquitectura actual?

Si la tienda virtual se implementa como una aplicación monolítica, el primer
problema es el acoplamiento entre funcionalidades. El catálogo, los clientes
y los pedidos comparten código, memoria y ciclo de despliegue. Por ello,
actualizar el catálogo —por ejemplo, modificar la forma de administrar precios
o existencias— puede exigir volver a probar y desplegar toda la aplicación,
incluida la funcionalidad de pedidos, aunque esta no haya sido modificada.

El segundo problema es la escalabilidad y el rendimiento general. Las
consultas de productos suelen ser mucho más frecuentes que la creación de
pedidos. En un monolito, esta alta demanda de consultas puede consumir los
recursos compartidos y producir lentitud general, afectando incluso a los
usuarios que intentan registrar o consultar pedidos. Además, no es posible
escalar únicamente el catálogo: se debe replicar toda la aplicación, aunque
la necesidad principal se encuentre en una sola funcionalidad.

El tercer problema corresponde al aislamiento de fallos. Un error de
programación o una saturación en una parte del sistema puede consumir recursos
compartidos y afectar a usuarios que intentan realizar operaciones no
relacionadas. Esto crea un punto de fallo amplio y dificulta la recuperación.

También existen dificultades organizacionales y de mantenimiento. Diferentes
equipos no pueden evolucionar con facilidad sus módulos de manera autónoma,
las liberaciones tienden a ser más grandes y el código puede acumular
dependencias cruzadas. Finalmente, el monolito puede dificultar la adopción de
tecnologías distintas o de estrategias de almacenamiento especializadas para
cada capacidad.

### 4.2 ¿Qué funcionalidades podrían convertirse en microservicios?

Las funcionalidades se pueden dividir de acuerdo con capacidades de negocio
cohesivas:

- **Catálogo de productos:** nombres, descripciones, precios y existencias.
- **Clientes:** registro, consulta, actualización y eliminación de datos de compradores.
- **Pedidos:** creación, consulta y actualización del estado de las órdenes.
- **Pagos:** validación del pedido asociado y registro de transacciones.
- **Inventario:** reserva y actualización de existencias, si el dominio exige
  separar esta responsabilidad del catálogo.
- **Notificaciones:** envío de correos o mensajes sobre el estado del pedido.

Para el alcance ampliado de este taller se implementan Productos, Clientes,
Pedidos y Pagos. La división permite demostrar comunicación síncrona,
validación distribuida, manejo de inventario, registro de pagos y aislamiento
de fallos.

### 4.3 ¿Qué responsabilidades tendría cada servicio?

**Productos** es responsable de administrar el catálogo. Registra nuevos
productos y permite consultar la colección completa o un producto por su
identificador. Es dueño de los datos de nombre, descripción, precio y stock.

**Clientes** es responsable de registrar, consultar, actualizar y eliminar
compradores. Mantiene los datos de identificación y contacto, y responde si un
cliente existe para que Pedidos pueda validar la orden.

**Pedidos** es responsable de recibir solicitudes de compra, consultar las
dependencias necesarias, calcular el total usando el precio entregado por
Productos y almacenar la orden con un estado inicial `pending`. También
permite consultar pedidos existentes y su estado.

Cada servicio debe modificar únicamente sus propios datos. Por ejemplo,
Pedidos no mantiene una copia editable de los clientes ni permite que el
cliente envíe el total definitivo; ambos valores son validados desde los
servicios propietarios.

### 4.4 ¿Cómo se comunicarían los servicios?

La comunicación se realiza mediante HTTP y APIs REST con mensajes JSON.
Pedidos consulta `GET /customers/{id}` en Clientes y
`GET /products/{id}` en Productos antes de crear una orden. Si las respuestas
son exitosas, valida las reglas de negocio y almacena el pedido. Si una
respuesta es `404`, informa que el recurso no existe. Si ocurre un timeout,
un error de conexión o una respuesta de servidor, devuelve `503` con un
mensaje que identifica la dependencia afectada.

Esta comunicación es síncrona y sencilla para el alcance académico. En un
sistema de mayor escala se podría complementar con eventos asíncronos para
notificaciones, reserva de inventario y procesos que no requieran bloquear la
respuesta del usuario.

### 4.5 ¿Qué ventajas tendría la nueva arquitectura?

La primera ventaja es la separación de responsabilidades. Cada servicio es
más pequeño, fácil de entender y puede evolucionar sin modificar toda la
aplicación. La segunda es la escalabilidad independiente: Productos podría
ejecutarse con más réplicas cuando el volumen de consultas aumente, sin
replicar necesariamente Clientes o Pedidos.

La tercera ventaja es el aislamiento de fallos. La caída de Productos impide
crear nuevos pedidos, porque no es seguro validar el precio o el stock, pero
no impide consultar clientes ni pedidos ya registrados. De esta manera el
sistema ofrece una degradación parcial en lugar de una interrupción completa.

También se obtiene independencia de despliegue, posibilidad de asignar
equipos por dominio y libertad para evolucionar tecnologías internas. Estas
ventajas deben equilibrarse con el costo de operar varios procesos, controlar
versiones de API y diagnosticar llamadas distribuidas.

## 5. Diagrama de arquitectura

El diagrama debe ubicar al Usuario o Aplicación Cliente como consumidor
principal y conectarlo con los cuatro microservicios: Productos en el puerto
`8001`, Clientes en el puerto `8002`, Pedidos en el puerto `8003` y Pagos en el
puerto `8004`. El cliente
puede consultar o registrar productos y clientes directamente mediante sus
APIs REST, mientras que utiliza Pedidos para registrar órdenes y consultar su
estado. Cada servicio mantiene sus propios datos en memoria y responde de
forma independiente a las solicitudes que le corresponden.

Durante la creación de un pedido, el servicio de Pedidos actúa como
coordinador. Primero realiza una llamada HTTP síncrona a Clientes mediante
`GET /customers/{id}` para comprobar que el comprador existe y luego consulta
Productos mediante `GET /products/{id}` para validar la existencia, el precio y
el stock. Si ambas respuestas son satisfactorias, calcula el total y registra
la orden. Si alguna dependencia no responde, Pedidos informa una degradación
controlada mediante timeout, manejo de excepciones y respuesta `503`, sin
impedir que los otros servicios continúen funcionando.

El flujo principal del diagrama es el siguiente:

```text
Usuario / Cliente
       |
       +--> Productos :8001   (consultar y registrar)
       |
       +--> Clientes :8002    (consultar y registrar)
       |
       +--> Pedidos :8003     (registrar y consultar pedidos)
       |
       +--> Pagos :8004       (registrar pagos)
                         |
                         +--> Productos :8001 (validar producto y precio)
                         +--> Clientes :8002  (validar cliente)
```

Pagos consulta a Pedidos mediante `GET /orders/{id}` antes de registrar una
transacción, evitando que se procese un pago para una orden inexistente.

Junto a Pedidos se debe anotar la estrategia de tolerancia a fallos:
`timeout de 2 segundos`, `try-except`, respuesta `503` y mensaje de
degradación. El diagrama debe mostrar que una flecha fallida hacia Productos
no elimina la disponibilidad de Clientes ni la consulta de pedidos existentes.

## 6. Descripción de responsabilidades

### 6.1 Microservicio de Productos

El archivo `products_service/main.py` implementa una API FastAPI con una lista
en memoria llamada `products`. Cada elemento contiene `id`, `name`,
`description`, `price` y `stock`.

Sus endpoints principales son:

- `GET /products`: devuelve todos los productos.
- `GET /products/{product_id}`: devuelve un producto concreto o `404`.
- `POST /products`: valida los datos, genera un identificador y registra el
  producto con respuesta `201`.
- `PUT /products/{product_id}`: actualiza los datos y el stock de un producto.
- `DELETE /products/{product_id}`: elimina un producto existente.
- `PATCH /products/stock`: valida y descuenta las cantidades solicitadas por
  un pedido.
- `PATCH /products/stock/restore`: devuelve al inventario las cantidades de
  un pedido eliminado.
- `GET /health`: confirma que el proceso está disponible.

El identificador es asignado internamente para impedir que el cliente altere
la identidad de un registro existente. FastAPI genera la documentación en
`http://localhost:8001/docs`.

### 6.2 Microservicio de Clientes

El archivo `customers_service/main.py` administra una lista en memoria llamada
`customers`. Cada cliente tiene `id`, `name`, `email`, `phone` y `address`.

Sus endpoints principales son:

- `GET /customers`: consulta todos los clientes.
- `GET /customers/{customer_id}`: consulta un cliente o devuelve `404`.
- `POST /customers`: valida y registra un cliente con identificador nuevo.
- `PUT /customers/{customer_id}`: actualiza los datos de un cliente existente.
- `DELETE /customers/{customer_id}`: elimina un cliente existente.
- `GET /health`: confirma que el proceso está disponible.

El servicio valida una estructura básica de correo electrónico y longitudes de
campos mediante modelos de Pydantic. La documentación está disponible en
`http://localhost:8002/docs`.

### 6.3 Microservicio de Pedidos

El archivo `orders_service/main.py` administra una lista `orders`. Para crear
una orden recibe `customer_id` y una lista de productos con cantidades. Antes
de guardar el registro:

1. Consulta al cliente en Clientes.
2. Consulta cada producto en Productos.
3. Comprueba que exista y que tenga stock suficiente.
4. Solicita a Productos el descuento de las cantidades del pedido.
5. Calcula el total a partir del precio del catálogo.
6. Guarda la orden con estado `pending` y fecha UTC.

Sus endpoints principales son:

- `GET /orders`: consulta las órdenes almacenadas.
- `GET /orders/{order_id}`: consulta una orden y su estado.
- `POST /orders`: valida dependencias y registra una orden.
- `PATCH /orders/{order_id}/status?new_status=confirmed`: actualiza el
  estado de una orden.
- `DELETE /orders/{order_id}`: elimina la orden y restaura sus cantidades en
  el inventario.
- `GET /health`: confirma que el servicio de Pedidos responde.

La función de comunicación encapsula los errores `TimeoutException`,
`RequestError`, `HTTPStatusError` y JSON inválido. En todos esos casos se
lanza `DependencyUnavailable`, que el endpoint transforma en una respuesta
`503` con información legible y el atributo `retryable: true`.

### 6.4 Dependencias entre servicios

Productos y Clientes son servicios independientes: no requieren llamadas a
otros componentes para atender sus operaciones principales. Pedidos depende
de ambos únicamente durante la creación de una orden. Esta dependencia se
implementa mediante llamadas HTTP síncronas a las APIs REST de Productos y
Clientes; Pedidos no accede directamente a sus listas internas ni modifica
sus datos. El descuento del inventario se ejecuta en Productos mediante
`PATCH /products/stock`, después de validar todas las cantidades. Si alguna
cantidad no está disponible, el servicio rechaza la operación completa y el
pedido no se guarda.

### 6.5 Microservicio de Pagos

El archivo `payments_service/main.py` administra una lista en memoria llamada
`payments`. Cada pago contiene `id`, `order_id`, `amount`, `method`, `status` y
`created_at`. Antes de registrar una transacción, el servicio consulta por
HTTP al microservicio de Pedidos para verificar que la orden exista. Si Pedidos
no responde, Pagos devuelve `503 Service Unavailable` con un mensaje de
degradación controlada.

Sus endpoints principales son:

- `GET /payments`: consulta los pagos registrados.
- `GET /payments/{payment_id}`: consulta un pago específico.
- `POST /payments`: valida el pedido y registra un pago aprobado.
- `PATCH /payments/{payment_id}/status`: actualiza el estado de un pago.
- `DELETE /payments/{payment_id}`: elimina un pago.
- `GET /health`: confirma que el servicio está disponible.

## 7. Respuestas a las preguntas orientadoras

### 7.1 ¿Cuál es la diferencia entre una arquitectura monolítica y una de microservicios?

Una arquitectura monolítica agrupa la mayoría de funcionalidades en una sola
aplicación desplegable. Sus módulos normalmente comparten proceso, memoria y
una estrategia de despliegue. Esto simplifica el inicio del proyecto, pero
puede aumentar el acoplamiento y hacer que cualquier cambio requiera liberar
la aplicación completa.

En una arquitectura de microservicios, la aplicación se divide en servicios
autónomos que representan capacidades de negocio. Cada servicio tiene una
responsabilidad delimitada, una API propia y, idealmente, control sobre sus
datos. La comunicación ocurre mediante protocolos de red, por lo que aparecen
nuevos retos: latencia, fallos parciales, compatibilidad de contratos,
observabilidad y coordinación distribuida.

La diferencia esencial no es únicamente el número de procesos, sino la
independencia de evolución, despliegue y escalamiento de cada capacidad.

### 7.2 ¿Por qué es importante que los microservicios tengan responsabilidades independientes?

La independencia reduce el acoplamiento y aumenta la cohesión. Cuando un
servicio tiene una responsabilidad clara, sus reglas de negocio, modelos y
pruebas son más fáciles de comprender. También se puede modificar o escalar
esa capacidad sin afectar directamente a las demás.

La independencia ayuda a limitar fallos. Un error en el catálogo no debería
eliminar la posibilidad de consultar clientes. Además, permite que los equipos
trabajen en paralelo con contratos explícitos, en lugar de modificar
continuamente un mismo módulo compartido.

Esta independencia debe ser real: no basta con crear carpetas separadas si
todos los componentes dependen de las mismas estructuras internas o de una
base de datos compartida sin límites de propiedad.

### 7.3 ¿Qué ventajas ofrece la comunicación mediante API REST?

REST utiliza HTTP, un protocolo ampliamente disponible y comprendido. Sus
recursos, métodos y códigos de estado ofrecen una convención clara para que
clientes escritos en lenguajes diferentes se comuniquen con los servicios.

En este taller, `GET` se usa para consultar recursos y `POST` para registrar
información. JSON facilita la interoperabilidad y FastAPI genera un contrato
OpenAPI que puede explorarse desde Swagger UI. HTTP también ofrece mecanismos
conocidos para timeouts, observación de latencia, autenticación y control de
errores.

REST no resuelve automáticamente la consistencia distribuida ni la seguridad.
Es necesario definir contratos compatibles, validar entradas, proteger los
endpoints y establecer políticas para reintentos y límites de tiempo.

### 7.4 ¿Qué sucede si uno de los microservicios deja de funcionar?

El efecto depende de si la operación necesita la dependencia. Si Productos
deja de funcionar, Productos no puede validarse y, por tanto, Pedidos no debe
crear nuevas órdenes con información incompleta o posiblemente incorrecta.
Sin embargo, Clientes puede continuar atendiendo consultas y Pedidos puede
consultar las órdenes que ya tiene en su lista local.

En esta implementación, el servicio de Pedidos usa un timeout de dos segundos
y captura las excepciones de conexión. En lugar de bloquearse o devolver un
error interno, responde `503 Service Unavailable` con el mensaje de que la
operación es temporalmente no disponible. Esto constituye una degradación
controlada: se pierde una capacidad específica, pero no se cae toda la
plataforma.

En un sistema productivo se complementarían estas medidas con circuit breaker,
reintentos limitados, colas, caché, réplicas, monitoreo y alertas.

### 7.5 ¿Cómo contribuyen los microservicios a la escalabilidad de una aplicación?

Permiten escalar horizontalmente la capacidad que concentra la demanda. Si
las consultas de catálogo son muy frecuentes, se pueden ejecutar más
instancias de Productos detrás de un balanceador sin aumentar necesariamente
el número de instancias de Clientes.

También permiten asignar recursos diferentes. Pedidos puede requerir mayor
capacidad de CPU durante campañas de venta, mientras que Clientes puede
mantener una configuración menor. La independencia facilita experimentar con
estrategias de caché, índices o tecnologías específicas para una sola
capacidad.

La escalabilidad no es automática. Se necesita descubrimiento de servicios,
balanceo, métricas, límites de recursos, automatización de despliegues y
pruebas de carga. Además, la comunicación entre servicios puede convertirse
en un cuello de botella si no se controlan los timeouts y las conexiones.

### 7.6 ¿Qué desafíos de seguridad y mantenimiento pueden presentarse al implementar esta arquitectura?

En seguridad, cada servicio expone una superficie de red adicional. Se deben
implementar autenticación y autorización, validar entradas en todos los
servicios, proteger secretos, aplicar HTTPS, controlar permisos entre
servicios y registrar auditorías. También es necesario configurar límites de
peticiones y evitar que un endpoint interno pueda ser utilizado como punto de
entrada no autorizado.

En mantenimiento, aumenta la cantidad de repositorios, procesos, archivos de
configuración y versiones de API. Una modificación de contrato puede romper
consumidores que no se actualicen al mismo tiempo. El diagnóstico es más
complejo porque una solicitud atraviesa varios procesos y puede fallar por
latencia o conectividad.

Por ello se requieren logs estructurados, métricas, trazabilidad distribuida,
health checks, pruebas de contrato, automatización CI/CD, documentación y
políticas explícitas de compatibilidad. También se debe administrar la
consistencia de datos y evitar transacciones distribuidas innecesarias.

## 8. Conclusiones técnicas

1. La división de la tienda virtual en Productos, Clientes y Pedidos permite
   aplicar una separación de responsabilidades clara. Cada servicio posee
   modelos y operaciones concretas, lo cual mejora la mantenibilidad y
   demuestra cómo una capacidad de negocio puede evolucionar de manera
   independiente.

2. La comunicación HTTP introduce fallos parciales que no existen dentro de
   una llamada local. La implementación de timeouts, excepciones controladas
   y respuestas `503` permite que Pedidos degrade únicamente la operación que
   necesita una dependencia caída, evitando esperas indefinidas y fallos en
   cascada.

3. Los microservicios ofrecen ventajas de escalabilidad y despliegue, pero no
   eliminan la complejidad: la trasladan a contratos, observabilidad, seguridad
   y operación distribuida. La solución desarrollada es adecuada como base
   académica; para producción debería incorporar persistencia independiente,
   autenticación, monitoreo, circuit breaker completo y estrategias de
   consistencia para inventario y transacciones.

## Referencias sugeridas

- Fowler, M. (2014). *Microservices*. Martin Fowler.
- Newman, S. (2021). *Building Microservices*. O'Reilly Media.
- Fielding, R. T. (2000). *Architectural Styles and the Design of
  Network-based Software Architectures*. University of California, Irvine.
- FastAPI. *FastAPI Documentation*.
- Richardson, C. (2018). *Microservices Patterns*. Manning Publications.
