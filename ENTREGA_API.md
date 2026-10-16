# Entrega — API GraphQL ARKEO Fleet (Catálogo de productos Seven)

**Proyecto:** Integración ARKEO Fleet — Seven / Phari Tech
**Tipo:** API GraphQL (AWS AppSync + Lambda Python + SQL Server)
**Región AWS:** us-east-2 (Ohio)
**Estado:** Desplegada y verificada end-to-end
**Fecha de entrega:** octubre 2026

---

## 1. Resumen

API GraphQL que expone el catálogo de productos del ERP **Seven** (SQL Server)
de forma segura, paginada y filtrable. Resuelve la consulta de negocio original
sobre las tablas `IN_PRODU` / `IN_TIPRO` / `IN_UNIME`, conservando sus campos,
relaciones y reglas:

- `EMP_CODI = 409`
- `LEFT(PRO_CO01, 1) = 7`
- `LEN(PRO_CO02) = 5`
- `LEN(PRO_CODI) >= 10`

Catálogo actual: **10.138 productos** (10.124 activos).

---

## 2. Datos de conexión

| Parámetro | Valor |
|---|---|
| **Endpoint (HTTP POST)** | `https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql` |
| **Método** | `POST` |
| **Autenticación** | API Key, header `x-api-key` |
| **API Key** | `<TU_API_KEY>` |
| **Content-Type** | `application/json` |
| **API ID (AppSync)** | `ufhb53oaaras3pugztjg5ektqu` |

> La API Key es de tipo prueba y tiene vencimiento (~6 meses). Para producción
> se recomienda migrar a Cognito User Pools o IAM (ver sección 9).

Ejemplo mínimo con `curl`:

```bash
curl -s -X POST \
  "https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql" \
  -H "Content-Type: application/json" \
  -H "x-api-key: <TU_API_KEY>" \
  -d '{"query":"query { productos(page:1, pageSize:5) { pagination { totalRegistros } } }"}'
```

---

## 3. Contrato GraphQL

### Query disponible

```graphql
productos(
  page: Int = 1
  pageSize: Int = 100
  filter: ProductoFilter
  orderBy: ProductoOrderBy = CODIGO_PRODUCTO_ASC
): ProductoConnection!
```

### Tipo de salida

```graphql
type ProductoConnection {
  data: [Producto!]!
  pagination: PageInfo!
}

type Producto {
  codigo_producto: String!       # PRO_CODI
  nombre_producto: String        # PRO_NOMB
  codigo_tipo: String            # IN_PRODU.TIP_CODI
  nombre_tipo: String            # IN_TIPRO.TIP_NOMB
  estado: String                 # ACTIVO / INACTIVO (PRO_ACTI)
  codigo_sistema: String         # PRO_CO01
  nombre_sistema: String         # PRO_NO01
  codigo_subsistema: String      # PRO_CO02
  nombre_subsistema: String      # PRO_NO02
  fecha_creacion: String         # PRO_FECR (ISO 8601)
  fecha_actualizacion: String    # IN_PRODU.AUD_UFAC (ISO 8601)
  codigo_unidad: String          # IN_UNIME.UNI_CODI
  nombre_unidad: String          # IN_UNIME.UNI_NOMB
  trabajo_repuesto: String       # TRABAJO / REPUESTO (regla sobre PRO_CO02)
}

type PageInfo {
  page: Int!
  pageSize: Int!
  totalRegistros: Int!
  totalPaginas: Int!
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
}
```

### Filtros (todos opcionales, se combinan con AND)

```graphql
input ProductoFilter {
  codigo_producto: String            # coincidencia exacta
  codigo_producto_contains: String   # coincidencia parcial (LIKE)
  nombre_producto_contains: String   # coincidencia parcial (LIKE)
  codigo_tipo: String
  estado: EstadoProducto             # ACTIVO | INACTIVO
  codigo_sistema: String
  codigo_subsistema: String
  codigo_unidad: String
  trabajo_repuesto: TrabajoRepuesto  # TRABAJO | REPUESTO
}

enum EstadoProducto { ACTIVO INACTIVO }
enum TrabajoRepuesto { TRABAJO REPUESTO }
```

> Los filtros se aplican **además** de las reglas de negocio originales; nunca
> las reemplazan.

### Ordenamiento (determinista)

```graphql
enum ProductoOrderBy {
  CODIGO_PRODUCTO_ASC    # por defecto
  CODIGO_PRODUCTO_DESC
  NOMBRE_PRODUCTO_ASC
  NOMBRE_PRODUCTO_DESC
  FECHA_CREACION_ASC
  FECHA_CREACION_DESC
}
```

Todo ordenamiento desempata por `codigo_producto` para garantizar resultados
estables entre páginas.

---

## 4. Paginación

- Paginación **real en SQL Server** con `OFFSET ... FETCH NEXT` (no carga todo
  en memoria).
- `page` es 1-based. `totalRegistros` y `totalPaginas` se calculan con `COUNT`.
- **Sin límite total**: se puede recorrer todo el catálogo avanzando de página.
- `pageSize` por defecto **100**, máximo **1000** (límite técnico configurable).
  Valores fuera de rango se normalizan automáticamente.

Para recorrer todo el catálogo: repetir la query incrementando `page` mientras
`pagination.hasNextPage` sea `true`.

---

## 5. Ejemplos de consumo

### Ejemplo 1 — Paginado básico

```graphql
query {
  productos(page: 1, pageSize: 100) {
    data {
      codigo_producto
      nombre_producto
      estado
      trabajo_repuesto
    }
    pagination {
      page
      pageSize
      totalRegistros
      totalPaginas
      hasNextPage
      hasPreviousPage
    }
  }
}
```

### Ejemplo 2 — Filtros + ordenamiento (con variables)

Query:
```graphql
query ($page:Int!, $size:Int!, $filter:ProductoFilter, $order:ProductoOrderBy) {
  productos(page:$page, pageSize:$size, filter:$filter, orderBy:$order) {
    data { codigo_producto nombre_producto trabajo_repuesto estado }
    pagination { totalRegistros totalPaginas hasNextPage }
  }
}
```
Variables:
```json
{
  "page": 1,
  "size": 50,
  "filter": { "estado": "ACTIVO", "trabajo_repuesto": "TRABAJO" },
  "order": "NOMBRE_PRODUCTO_ASC"
}
```

### Ejemplo 3 — Búsqueda parcial por nombre

```graphql
query {
  productos(page: 1, pageSize: 20, filter: { nombre_producto_contains: "TURBO" }) {
    data { codigo_producto nombre_producto }
    pagination { totalRegistros totalPaginas }
  }
}
```

### Ejemplo 4 — Selección mínima de campos (consulta flexible)

```graphql
query {
  productos(page: 2, pageSize: 25) {
    data { codigo_producto }
    pagination { totalRegistros totalPaginas }
  }
}
```

---

## 6. Respuesta de ejemplo

```json
{
  "data": {
    "productos": {
      "data": [
        {
          "codigo_producto": "70M0101001",
          "nombre_producto": "AA005- D/M TURBO MOTOR CAMBIAR EMPAQUES",
          "estado": "ACTIVO",
          "trabajo_repuesto": "TRABAJO"
        }
      ],
      "pagination": {
        "page": 1,
        "pageSize": 100,
        "totalRegistros": 10138,
        "totalPaginas": 102,
        "hasNextPage": true,
        "hasPreviousPage": false
      }
    }
  }
}
```

---

## 7. Pruebas con Postman

1. Importar el archivo `postman_collection.json` (incluido en la entrega).
2. Las variables de colección `appsync_url` y `api_key` ya vienen cargadas con
   los valores reales; no requiere configuración adicional.
3. Ejecutar cualquiera de las requests. Cada una incluye **tests automáticos**
   (pestaña *Test Results*) que validan código HTTP, ausencia de errores y la
   lógica esperada (p.ej. que el filtro `ACTIVO` solo devuelva activos).

Requests incluidas:

| # | Nombre | Qué valida |
|---|---|---|
| 01 | Paginado básico | estructura y metadatos de paginación |
| 02 | Todos los campos (variables) | proyección completa y respeto de `pageSize` |
| 03 | Filtro estado ACTIVO | solo devuelve activos |
| 04 | Filtro TRABAJO + orden | solo tipo TRABAJO, ordenado |
| 05 | Búsqueda por nombre (contains) | coincidencia parcial |
| 06 | Selección mínima de campos | consulta flexible |
| 07 | Error de auth (sin API key) | rechazo 401 sin credenciales |

---

## 8. Arquitectura y recursos AWS

```
Cliente (Postman / app)
      │  POST /graphql  (x-api-key)
      ▼
AWS AppSync  (arkeo-fleet-graphql, auth API_KEY)
      │  Invoke
      ▼
AWS Lambda  (arkeo-fleet-graphql-productos-resolver, Python 3.12, en VPC)
      │  SQL parametrizado + OFFSET/FETCH
      ├── Secrets Manager: seven-db-credentials (solo lectura)
      ▼
SQL Server on-prem  10.125.18.16:1433  (vía VPN / Virtual Private Gateway)
```

### Recursos creados por el stack `arkeo-fleet-graphql`

| Recurso | Nombre / Identificador |
|---|---|
| AppSync GraphQL API | `arkeo-fleet-graphql` (`ufhb53oaaras3pugztjg5ektqu`) |
| Lambda resolver | `arkeo-fleet-graphql-productos-resolver` (Python 3.12) |
| Data source | `ProductosLambdaDataSource` (AWS_LAMBDA) |
| Resolver | `Query.productos` |
| IAM Role Lambda | mínimo privilegio (lectura del secret + ENIs de VPC) |
| IAM Role AppSync→Lambda | invoca solo esta Lambda |
| IAM Role AppSync→Logs | escritura de logs en CloudWatch |
| Log Group | `/aws/lambda/arkeo-fleet-graphql-productos-resolver` (14 días) |

### Recursos reutilizados (existentes, no modificados)

| Recurso | Identificador |
|---|---|
| VPC | `vpc-01c7cedbf7ffc4bda` (vigia-vpc) |
| Subnets privadas | `subnet-0fbaebb0a7171c1f0`, `subnet-01aadaa8cf1526d54` |
| Security Group | `sg-006aea4d75d0b9d54` (seven-api-lambda-sg) |
| Secret | `seven-db-credentials` |
| Conectividad SQL | VPN / Virtual Private Gateway (ruta `10.125.18.0/24`) |

---

## 9. Seguridad

- **Credenciales en Secrets Manager**, nunca en código ni en variables de
  entorno en texto plano. Se cachean en memoria del contenedor Lambda.
- **IAM de mínimo privilegio** en todos los roles (la Lambda solo puede leer el
  secret `seven-db-credentials`; AppSync solo puede invocar esta Lambda).
- **Consultas 100% parametrizadas** — ningún valor de usuario se concatena en el
  SQL; el `ORDER BY` usa lista blanca de columnas. Protegido contra inyección.
- **Manejo seguro de errores** — el detalle técnico queda en CloudWatch; al
  cliente se le devuelve un mensaje genérico sin exponer SQL ni credenciales.
- **Lambda en subnets privadas** — sin IP pública; alcanza SQL Server por VPN.

### Recomendación para producción

Migrar la autenticación de `API_KEY` a **Amazon Cognito** o **IAM** para
control de acceso por usuario/rol y evitar la rotación manual de API keys.

---

## 10. Operación y mantenimiento

### Verificación end-to-end realizada

| Escenario | Resultado |
|---|---|
| Paginación (10.138 registros, páginas distintas) | OK |
| Filtro estado ACTIVO (10.124) | OK |
| Filtro trabajo_repuesto TRABAJO (2.500) | OK |
| Búsqueda parcial "TURBO" (126) | OK |
| Selección flexible de campos | OK |
| Rechazo sin API key | OK |

### Límites técnicos

- Timeout Lambda: 29 s (alineado con el máximo de integración de AppSync).
- `pageSize` máximo: 1000 (configurable en `template.yaml`).
- La Lambda reutiliza la conexión SQL entre invocaciones (warm start).

### Logs

CloudWatch Logs: grupo `/aws/lambda/arkeo-fleet-graphql-productos-resolver`
(retención 14 días). El nivel de log de campo en AppSync está en `ERROR`.

### Obtener / rotar el API Key

```bash
aws appsync list-api-keys --api-id ufhb53oaaras3pugztjg5ektqu --region us-east-2
aws appsync create-api-key --api-id ufhb53oaaras3pugztjg5ektqu --region us-east-2
```

### Re-desplegar tras cambios de código

```bash
sam build
sam deploy
```

### Eliminar el stack (no afecta VPC, subnets, SG ni secret)

```bash
sam delete --stack-name arkeo-fleet-graphql --region us-east-2
```

---

## 11. Contenido del entregable

| Archivo | Descripción |
|---|---|
| `ENTREGA_API.md` | Este documento |
| `README.md` | Guía técnica de configuración y despliegue |
| `postman_collection.json` | Colección Postman lista para importar |
| `schema.graphql` | Esquema GraphQL |
| `template.yaml` | Infraestructura (SAM/CloudFormation) |
| `src/` | Código Lambda (handler, config, query builder, database) |
| `resolvers/` | Plantillas VTL del resolver |
| `tests/` | Pruebas unitarias y de integración |
