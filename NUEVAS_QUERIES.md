# Nuevas Funcionalidades - API GraphQL ARKEO

## Resumen de cambios

Se han agregado dos nuevas queries al esquema GraphQL para cumplir con los requerimientos de:

1. **Consulta de productos inactivos** - `productosInactivos`
2. **Consulta de grupos y subgrupos únicos** - `sistemasSubsistemas`

---

## 1. Query: productosInactivos

### Descripción
Consulta paginada de productos con estado **INACTIVO**. Funciona igual que la query `productos` pero filtra automáticamente solo productos inactivos (PRO_ACTI <> 'A').

### Sintaxis

```graphql
productosInactivos(
  page: Int = 1
  pageSize: Int = 100
  filter: ProductoInactivoFilter
  orderBy: ProductoOrderBy = CODIGO_PRODUCTO_ASC
): ProductoConnection!
```

### Filtros disponibles

El tipo `ProductoInactivoFilter` es igual a `ProductoFilter` pero **sin** el campo `estado` (ya que se aplica automáticamente):

```graphql
input ProductoInactivoFilter {
  codigo_producto: String
  codigo_producto_contains: String
  nombre_producto_contains: String
  codigo_tipo: String
  codigo_sistema: String
  codigo_subsistema: String
  codigo_unidad: String
  trabajo_repuesto: TrabajoRepuesto
}
```

### Ejemplo 1: Listar todos los productos inactivos

**Formato GraphQL:**
```graphql
query {
  productosInactivos(page: 1, pageSize: 50) {
    data {
      codigo_producto
      nombre_producto
      estado
      codigo_sistema
      nombre_sistema
      codigo_subsistema
      nombre_subsistema
      fecha_actualizacion
    }
    pagination {
      page
      pageSize
      totalRegistros
      totalPaginas
      hasNextPage
    }
  }
}
```

**Formato JSON (para Postman/API):**
```json
{
  "query": "query ListarInactivos($page: Int!, $pageSize: Int!) { productosInactivos(page: $page, pageSize: $pageSize) { data { codigo_producto nombre_producto estado codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema fecha_actualizacion } pagination { page pageSize totalRegistros totalPaginas hasNextPage } } }",
  "variables": {
    "page": 1,
    "pageSize": 50
  }
}
```

### Ejemplo 2: Productos inactivos de tipo TRABAJO

**Formato GraphQL:**
```graphql
query {
  productosInactivos(
    page: 1
    pageSize: 100
    filter: { trabajo_repuesto: TRABAJO }
    orderBy: FECHA_CREACION_DESC
  ) {
    data {
      codigo_producto
      nombre_producto
      trabajo_repuesto
      fecha_creacion
    }
    pagination {
      totalRegistros
    }
  }
}
```

**Formato JSON (para Postman/API):**
```json
{
  "query": "query InactivosTrabajo($page: Int!, $pageSize: Int!, $filter: ProductoInactivoFilter, $orderBy: ProductoOrderBy) { productosInactivos(page: $page, pageSize: $pageSize, filter: $filter, orderBy: $orderBy) { data { codigo_producto nombre_producto trabajo_repuesto fecha_creacion } pagination { totalRegistros } } }",
  "variables": {
    "page": 1,
    "pageSize": 100,
    "filter": {
      "trabajo_repuesto": "TRABAJO"
    },
    "orderBy": "FECHA_CREACION_DESC"
  }
}
```

### Ejemplo 3: Buscar productos inactivos por nombre

**Formato GraphQL:**
```graphql
query {
  productosInactivos(
    page: 1
    pageSize: 25
    filter: { nombre_producto_contains: "MOTOR" }
  ) {
    data {
      codigo_producto
      nombre_producto
      estado
    }
    pagination {
      totalRegistros
      totalPaginas
    }
  }
}
```

**Formato JSON (para Postman/API):**
```json
{
  "query": "query BuscarInactivos($page: Int!, $pageSize: Int!, $filter: ProductoInactivoFilter) { productosInactivos(page: $page, pageSize: $pageSize, filter: $filter) { data { codigo_producto nombre_producto estado } pagination { totalRegistros totalPaginas } } }",
  "variables": {
    "page": 1,
    "pageSize": 25,
    "filter": {
      "nombre_producto_contains": "MOTOR"
    }
  }
}
```

---

## 2. Query: sistemasSubsistemas

### Descripción
Devuelve una lista **ÚNICA (DISTINCT)** de todos los sistemas (grupos) y subsistemas disponibles en el catálogo de productos. 

Esta query es útil para:
- Poblar filtros desplegables en interfaces de usuario
- Obtener el catálogo de grupos y subgrupos sin duplicados
- Conocer la estructura organizacional de productos

**Nota importante:** Esta query **NO está paginada** ya que devuelve un conjunto de datos relativamente pequeño (solo combinaciones únicas de sistema/subsistema).

### Sintaxis

```graphql
sistemasSubsistemas(
  orderBy: SistemaOrderBy = CODIGO_SISTEMA_ASC
): [SistemaSubsistema!]!
```

### Tipo de retorno

```graphql
type SistemaSubsistema {
  codigo_sistema: String!
  nombre_sistema: String!
  codigo_subsistema: String!
  nombre_subsistema: String!
}
```

### Ordenamiento disponible

```graphql
enum SistemaOrderBy {
  CODIGO_SISTEMA_ASC        # Por defecto
  CODIGO_SISTEMA_DESC
  NOMBRE_SISTEMA_ASC
  NOMBRE_SISTEMA_DESC
  CODIGO_SUBSISTEMA_ASC
  CODIGO_SUBSISTEMA_DESC
}
```

### Ejemplo 1: Listar todos los sistemas y subsistemas

**Formato GraphQL:**
```graphql
query {
  sistemasSubsistemas {
    codigo_sistema
    nombre_sistema
    codigo_subsistema
    nombre_subsistema
  }
}
```

**Formato JSON (para Postman/API):**
```json
{
  "query": "query { sistemasSubsistemas { codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema } }"
}
```

### Ejemplo 2: Ordenar por nombre de sistema

**Formato GraphQL:**
```graphql
query {
  sistemasSubsistemas(orderBy: NOMBRE_SISTEMA_ASC) {
    codigo_sistema
    nombre_sistema
    codigo_subsistema
    nombre_subsistema
  }
}
```

**Formato JSON (para Postman/API):**
```json
{
  "query": "query ObtenerGruposYSubgrupos($orderBy: SistemaOrderBy) { sistemasSubsistemas(orderBy: $orderBy) { codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema } }",
  "variables": {
    "orderBy": "NOMBRE_SISTEMA_ASC"
  }
}
```

### Ejemplo 3: Solo códigos (para poblar un filtro)

**Formato GraphQL:**
```graphql
query {
  sistemasSubsistemas {
    codigo_sistema
    codigo_subsistema
  }
}
```

**Formato JSON (para Postman/API):**
```json
{
  "query": "query { sistemasSubsistemas { codigo_sistema codigo_subsistema } }"
}
```

### Ejemplo de respuesta

```json
{
  "data": {
    "sistemasSubsistemas": [
      {
        "codigo_sistema": "7A001",
        "nombre_sistema": "SISTEMA HIDRAULICO",
        "codigo_subsistema": "7A00M",
        "nombre_subsistema": "MANGUERAS HIDRAULICAS"
      },
      {
        "codigo_sistema": "7A001",
        "nombre_sistema": "SISTEMA HIDRAULICO",
        "codigo_subsistema": "7A00R",
        "nombre_subsistema": "REPUESTOS HIDRAULICOS"
      },
      {
        "codigo_sistema": "7B002",
        "nombre_sistema": "SISTEMA ELECTRICO",
        "codigo_subsistema": "7B00M",
        "nombre_subsistema": "MOTORES ELECTRICOS"
      }
    ]
  }
}
```

---

## 3. Comparación: productos vs productosInactivos

| Característica | productos | productosInactivos |
|---|---|---|
| Paginación | ✅ Sí | ✅ Sí |
| Filtro de estado | `estado: ACTIVO/INACTIVO` | Forzado a INACTIVO |
| Filtros adicionales | Todos | Todos excepto `estado` |
| Ordenamiento | Todos | Todos |
| Uso típico | Catálogo general | Inactivaciones/histórico |

---

## 4. Ejemplos combinados - Formato JSON completo

### Caso de uso: Interfaz con filtros dinámicos

#### Paso 1: Cargar los sistemas y subsistemas disponibles para poblar filtros

```json
{
  "query": "query ObtenerFiltros($orderBy: SistemaOrderBy) { sistemasSubsistemas(orderBy: $orderBy) { codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema } }",
  "variables": {
    "orderBy": "NOMBRE_SISTEMA_ASC"
  }
}
```

#### Paso 2: El usuario selecciona un sistema en el filtro y consulta productos

```json
{
  "query": "query ProductosDelSistema($page: Int!, $pageSize: Int!, $filter: ProductoFilter) { productos(page: $page, pageSize: $pageSize, filter: $filter) { data { codigo_producto nombre_producto codigo_subsistema nombre_subsistema } pagination { totalRegistros hasNextPage } } }",
  "variables": {
    "page": 1,
    "pageSize": 100,
    "filter": {
      "estado": "ACTIVO",
      "codigo_sistema": "70"
    }
  }
}
```

#### Paso 3: Ver los productos inactivos del mismo sistema

```json
{
  "query": "query InactivosDelSistema($page: Int!, $pageSize: Int!, $filter: ProductoInactivoFilter) { productosInactivos(page: $page, pageSize: $pageSize, filter: $filter) { data { codigo_producto nombre_producto fecha_actualizacion } pagination { totalRegistros } } }",
  "variables": {
    "page": 1,
    "pageSize": 100,
    "filter": {
      "codigo_sistema": "70"
    }
  }
}
```

---

## 5. Implementación técnica

### Cambios en el esquema (schema.graphql)
- Agregado tipo `SistemaSubsistema`
- Agregado input `ProductoInactivoFilter`
- Agregado enum `SistemaOrderBy`
- Agregadas queries `productosInactivos` y `sistemasSubsistemas`

### Cambios en el código (src/)
- **query_builder.py**: 
  - Modificada función `_build_dynamic_filters` con parámetro `force_inactive`
  - Agregada función `build_sistemas_subsistemas_query`
  - Agregados mapas de ordenamiento para sistemas/subsistemas
  
- **handler.py**:
  - Agregado resolver `_resolve_productos_inactivos`
  - Agregado resolver `_resolve_sistemas_subsistemas`
  
- **database.py**:
  - Agregada función `fetch_all` para consultas sin paginación

### Nuevos resolvers VTL
- `Query.productosInactivos.request.vtl`
- `Query.productosInactivos.response.vtl`
- `Query.sistemasSubsistemas.request.vtl`
- `Query.sistemasSubsistemas.response.vtl`

### Cambios en infraestructura (template.yaml)
- Agregados recursos `ProductosInactivosResolver` y `SistemasSubsistemasResolver`

---

## 6. Despliegue

Para desplegar las nuevas funcionalidades:

```powershell
sam build
sam deploy
```

Las nuevas queries estarán disponibles inmediatamente en el mismo endpoint GraphQL.

---

## 7. Pruebas

### Prueba manual en Postman

1. Importar la colección `postman_collection.json` (actualizada)
2. Ejecutar la request "07 - Productos Inactivos"
3. Ejecutar la request "08 - Sistemas y Subsistemas"

### Prueba manual con curl

**Productos inactivos:**
```bash
curl -X POST "https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql" \
  -H "Content-Type: application/json" \
  -H "x-api-key: <TU_API_KEY>" \
  -d '{"query":"query { productosInactivos(page:1, pageSize:10) { data { codigo_producto nombre_producto estado } pagination { totalRegistros } } }"}'
```

**Sistemas y subsistemas:**
```bash
curl -X POST "https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql" \
  -H "Content-Type: application/json" \
  -H "x-api-key: <TU_API_KEY>" \
  -d '{"query":"query { sistemasSubsistemas { codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema } }"}'
```

---

## 8. Beneficios

### ✅ Sin duplicados
La query `sistemasSubsistemas` usa `SELECT DISTINCT` para garantizar que no haya grupos/subgrupos duplicados.

### ✅ Rendimiento optimizado
- `productosInactivos`: Usa el mismo mecanismo de paginación eficiente con OFFSET/FETCH
- `sistemasSubsistemas`: Consulta ligera sin paginación (conjunto pequeño de datos únicos)

### ✅ Mantiene todas las garantías de seguridad
- Consultas 100% parametrizadas
- ORDER BY con lista blanca
- Mismas reglas de negocio del query base

### ✅ Compatible con el API existente
- No rompe queries existentes
- Reutiliza la misma infraestructura y conexión a base de datos
- Mismo endpoint y autenticación
