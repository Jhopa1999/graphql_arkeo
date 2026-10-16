# ARKEO Fleet — API GraphQL (AppSync + Lambda Python + SQL Server)

API GraphQL que expone el catálogo de productos del ERP **Seven** (SQL Server)
mediante **AWS AppSync**, resuelta por una **Lambda Python** desplegada en VPC
que consulta la base con **paginación real** y **filtros dinámicos**.

La base del desarrollo es la consulta `SELECT` original sobre `IN_PRODU` /
`IN_TIPRO` / `IN_UNIME`, conservando sus campos, relaciones, filtros y reglas
de negocio (`EMP_CODI = 409`, `LEFT(PRO_CO01,1)=7`, `LEN(PRO_CO02)=5`,
`LEN(PRO_CODI) >= 10`).

---

## Arquitectura

```
Cliente (Postman)
      │  POST /graphql  (header x-api-key)
      ▼
AWS AppSync  ── esquema GraphQL, API Key, resolver VTL
      │  Invoke
      ▼
AWS Lambda (Python 3.12, en VPC)
      │  (pytds, SQL parametrizado, OFFSET/FETCH)
      ├── Secrets Manager: seven-db-credentials  (solo lectura)
      ▼
SQL Server on-prem  10.125.18.16:1433  (vía VPN / Virtual Private Gateway)
```

- **Paginación real en SQL Server** con `OFFSET ... FETCH NEXT` (no se cargan
  todos los registros en memoria). `COUNT(1)` calcula el total para los
  metadatos. Sin límite global: se recorre todo el catálogo por páginas.
- **Filtros dinámicos** opcionales que se añaden con `AND` sobre las reglas de
  negocio originales, nunca las reemplazan.
- **Consultas flexibles**: cada cliente GraphQL pide solo los campos que usa.
- **Ordenamiento determinista**: la columna elegida + `PRO_CODI` como desempate.

### Campos expuestos (tipo `Producto`)

| GraphQL | Origen SQL |
|---|---|
| `codigo_producto` | `PRO_CODI` |
| `nombre_producto` | `PRO_NOMB` |
| `codigo_tipo` | `IN_PRODU.TIP_CODI` |
| `nombre_tipo` | `IN_TIPRO.TIP_NOMB` |
| `estado` | `CASE PRO_ACTI='A' → ACTIVO / INACTIVO` |
| `codigo_sistema` | `PRO_CO01` |
| `nombre_sistema` | `PRO_NO01` |
| `codigo_subsistema` | `PRO_CO02` |
| `nombre_subsistema` | `PRO_NO02` |
| `fecha_creacion` | `PRO_FECR` |
| `fecha_actualizacion` | `IN_PRODU.AUD_UFAC` |
| `codigo_unidad` | `IN_UNIME.UNI_CODI` |
| `nombre_unidad` | `IN_UNIME.UNI_NOMB` |
| `trabajo_repuesto` | `CASE PRO_CO02 LIKE '%M%' → TRABAJO / REPUESTO` |

---

## Estructura del proyecto

```
graphql_arkeo/
├── template.yaml                 # Infraestructura SAM/CloudFormation
├── samconfig.toml                # Parámetros de despliegue (región us-east-2)
├── schema.graphql                # Esquema GraphQL de AppSync
├── resolvers/
│   ├── Query.productos.request.vtl
│   └── Query.productos.response.vtl
├── src/                          # Código Lambda (raíz del paquete desplegado)
│   ├── handler.py                # Entry point AppSync, paginación y despacho
│   ├── config.py                 # Credenciales (Secrets Manager) y límites
│   ├── query_builder.py          # SQL parametrizado (reglas + filtros + paginación)
│   ├── database.py               # Conexión pytds y ejecución
│   └── requirements.txt          # python-tds
├── tests/                        # Unitarias + integración (gated)
├── postman_collection.json       # Colección Postman lista para importar
└── README.md
```

---

## Recursos AWS

### Reutilizados (ya existentes — no se crean ni modifican)

| Recurso | Identificador | Uso |
|---|---|---|
| VPC | `vpc-01c7cedbf7ffc4bda` (vigia-vpc) | Red |
| Subnet privada A | `subnet-0fbaebb0a7171c1f0` (us-east-2a) | Lambda ENI |
| Subnet privada B | `subnet-01aadaa8cf1526d54` (us-east-2b) | Lambda ENI |
| Security Group | `sg-006aea4d75d0b9d54` (seven-api-lambda-sg) | Egress a SQL Server |
| Secret | `seven-db-credentials` | Credenciales SQL Server |

> Las subnets privadas tienen ruta `10.125.18.0/24 → vgw-...` (VPN) hacia el
> SQL Server on-prem, y NAT para alcanzar Secrets Manager. No se requiere NAT
> ni VPC nuevos.

### Creados por el stack

- **Lambda** `arkeo-fleet-graphql-productos-resolver` (Python 3.12, en VPC).
- **IAM Role** de la Lambda (mínimo privilegio: `GetSecretValue` solo sobre
  `seven-db-credentials` + managed policy de ENIs de VPC).
- **AppSync GraphQLApi** `arkeo-fleet-graphql` (auth `API_KEY`) + schema + API key.
- **IAM Role** para que AppSync invoque únicamente esta Lambda.
- **IAM Role** para que AppSync escriba logs en CloudWatch.
- **Log Group** de la Lambda (retención 14 días).

---

## Seguridad

- Credenciales **solo en Secrets Manager**, nunca en código ni en variables de
  entorno en texto plano. Se cachean en memoria del contenedor.
- **IAM de mínimo privilegio** en todos los roles.
- **Consultas 100% parametrizadas** (`pyformat`): ningún valor de usuario se
  concatena en el SQL. El `ORDER BY` usa lista blanca de columnas.
- **Manejo seguro de errores**: el detalle se registra en CloudWatch; al cliente
  se le devuelve un mensaje genérico (sin SQL, credenciales ni stack traces).

---

## Requisitos previos

- AWS CLI configurado (`aws configure`) con la cuenta y región `us-east-2`.
- AWS SAM CLI y Python 3.12.
- Permisos para crear Lambda, IAM, AppSync y Logs en la cuenta.

---

## Pruebas

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pytest boto3
.\.venv\Scripts\python.exe -m pytest -q
```

- **Unitarias** (siempre): reglas de negocio, filtros, paginación,
  anti-inyección, cálculo de `pagination` y enmascaramiento de errores.
- **Integración** (opcionales, se omiten si no hay entorno):
  - Base de datos: requiere VPN + secret.
    ```powershell
    $env:RUN_DB_INTEGRATION="1"; python -m pytest tests/test_integration.py -q
    ```
  - GraphQL extremo a extremo: tras desplegar.
    ```powershell
    $env:RUN_GRAPHQL_INTEGRATION="1"
    $env:APPSYNC_URL="<GraphQLApiUrl>"
    $env:APPSYNC_API_KEY="<GraphQLApiKey>"
    python -m pytest tests/test_integration.py -q
    ```

---

## Despliegue

```powershell
sam build
sam deploy --guided        # primera vez (confirma parámetros y crea el stack)
# siguientes veces:
sam deploy
```

Los parámetros por defecto (`template.yaml`) ya apuntan a los recursos
existentes verificados. Al terminar, SAM imprime los **Outputs**:

- `GraphQLApiUrl` — endpoint para Postman.
- `GraphQLApiKey` — valor del header `x-api-key`.
- `GraphQLApiId`, `ResolverFunctionArn`.

Para recuperar el API Key más tarde:

```powershell
aws appsync list-api-keys --api-id <GraphQLApiId> --region us-east-2
```

---

## Consumo desde Postman

1. Importa `postman_collection.json`.
2. En las variables de la colección, define:
   - `appsync_url` = `GraphQLApiUrl` del output.
   - `api_key` = `GraphQLApiKey` del output.
3. Ejecuta cualquiera de las requests. Todas son `POST` con:
   - Header `Content-Type: application/json`
   - Header `x-api-key: {{api_key}}`

### Ejemplo de query

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

### Con filtros y ordenamiento

```graphql
query {
  productos(
    page: 1
    pageSize: 50
    filter: { estado: ACTIVO, trabajo_repuesto: REPUESTO, nombre_producto_contains: "ACEITE" }
    orderBy: NOMBRE_PRODUCTO_ASC
  ) {
    data { codigo_producto nombre_producto }
    pagination { totalRegistros totalPaginas hasNextPage }
  }
}
```

**Filtros disponibles** (`ProductoFilter`, todos opcionales):
`codigo_producto`, `codigo_producto_contains`, `nombre_producto_contains`,
`codigo_tipo`, `estado` (`ACTIVO`/`INACTIVO`), `codigo_sistema`,
`codigo_subsistema`, `codigo_unidad`, `trabajo_repuesto` (`TRABAJO`/`REPUESTO`).

**Ordenamientos** (`ProductoOrderBy`): `CODIGO_PRODUCTO_ASC` (default),
`CODIGO_PRODUCTO_DESC`, `NOMBRE_PRODUCTO_ASC`, `NOMBRE_PRODUCTO_DESC`,
`FECHA_CREACION_ASC`, `FECHA_CREACION_DESC`.

---

## Límites técnicos y rendimiento

- `pageSize` por defecto **100**, máximo **1000** (configurable en
  `template.yaml`: `DefaultPageSize` / `MaxPageSize`). No hay límite total de
  registros: se recorre todo mediante páginas.
- Timeout Lambda: 29 s (alineado con el máximo de integración de AppSync).
- La Lambda reutiliza la conexión SQL entre invocaciones (warm start) y la
  reconstruye si queda en mal estado.

---

## Eliminar el stack

```powershell
sam delete --stack-name arkeo-fleet-graphql --region us-east-2
```

Esto elimina únicamente los recursos creados por el stack; **no** toca la VPC,
subnets, security group ni el secret reutilizados.
