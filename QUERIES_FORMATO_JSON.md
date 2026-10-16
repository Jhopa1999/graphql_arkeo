# Queries en Formato JSON - API GraphQL ARKEO

Este documento contiene todos los queries en formato JSON listo para usar en Postman, cURL o cualquier cliente HTTP.

**Endpoint**: `https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql`  
**API Key**: `da2-lagw6sktkbe5zca5zcqmw5e3oi`  
**Método**: POST  
**Headers**:
- `Content-Type: application/json`
- `x-api-key: da2-lagw6sktkbe5zca5zcqmw5e3oi`

---

## 1. Productos (catálogo general)

### 1.1. Listar productos activos

```json
{
  "query": "query ListarProductos($page: Int!, $pageSize: Int!, $filter: ProductoFilter) { productos(page: $page, pageSize: $pageSize, filter: $filter) { data { codigo_producto nombre_producto estado trabajo_repuesto } pagination { page pageSize totalRegistros totalPaginas hasNextPage } } }",
  "variables": {
    "page": 1,
    "pageSize": 50,
    "filter": {
      "estado": "ACTIVO"
    }
  }
}
```

### 1.2. Buscar productos por nombre

```json
{
  "query": "query BuscarProductos($page: Int!, $pageSize: Int!, $filter: ProductoFilter) { productos(page: $page, pageSize: $pageSize, filter: $filter) { data { codigo_producto nombre_producto } pagination { totalRegistros totalPaginas } } }",
  "variables": {
    "page": 1,
    "pageSize": 20,
    "filter": {
      "nombre_producto_contains": "TURBO"
    }
  }
}
```

### 1.3. Filtrar por sistema y estado

```json
{
  "query": "query ProductosPorSistema($page: Int!, $pageSize: Int!, $filter: ProductoFilter) { productos(page: $page, pageSize: $pageSize, filter: $filter) { data { codigo_producto nombre_producto codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema } pagination { totalRegistros } } }",
  "variables": {
    "page": 1,
    "pageSize": 100,
    "filter": {
      "codigo_sistema": "70",
      "estado": "ACTIVO"
    }
  }
}
```

---

## 2. Productos Inactivos (nuevo)

### 2.1. Listar todos los productos inactivos

```json
{
  "query": "query ListarInactivos($page: Int!, $pageSize: Int!) { productosInactivos(page: $page, pageSize: $pageSize) { data { codigo_producto nombre_producto estado fecha_actualizacion } pagination { page pageSize totalRegistros totalPaginas hasNextPage } } }",
  "variables": {
    "page": 1,
    "pageSize": 50
  }
}
```

### 2.2. Productos inactivos de tipo TRABAJO

```json
{
  "query": "query InactivosTrabajo($page: Int!, $pageSize: Int!, $filter: ProductoInactivoFilter) { productosInactivos(page: $page, pageSize: $pageSize, filter: $filter) { data { codigo_producto nombre_producto trabajo_repuesto fecha_creacion } pagination { totalRegistros } } }",
  "variables": {
    "page": 1,
    "pageSize": 100,
    "filter": {
      "trabajo_repuesto": "TRABAJO"
    }
  }
}
```

### 2.3. Buscar productos inactivos por nombre

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

### 2.4. Inactivos por sistema (ordenados por fecha)

```json
{
  "query": "query InactivosPorSistema($page: Int!, $pageSize: Int!, $filter: ProductoInactivoFilter, $orderBy: ProductoOrderBy) { productosInactivos(page: $page, pageSize: $pageSize, filter: $filter, orderBy: $orderBy) { data { codigo_producto nombre_producto codigo_sistema nombre_sistema fecha_actualizacion } pagination { totalRegistros } } }",
  "variables": {
    "page": 1,
    "pageSize": 50,
    "filter": {
      "codigo_sistema": "70"
    },
    "orderBy": "FECHA_CREACION_DESC"
  }
}
```

---

## 3. Sistemas y Subsistemas (grupos únicos - nuevo)

### 3.1. Listar todos (sin duplicados)

```json
{
  "query": "query { sistemasSubsistemas { codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema } }"
}
```

### 3.2. Ordenar por código de sistema

```json
{
  "query": "query ObtenerGrupos($orderBy: SistemaOrderBy) { sistemasSubsistemas(orderBy: $orderBy) { codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema } }",
  "variables": {
    "orderBy": "CODIGO_SISTEMA_ASC"
  }
}
```

### 3.3. Ordenar por nombre de sistema (alfabético)

```json
{
  "query": "query ObtenerGruposOrdenados($orderBy: SistemaOrderBy) { sistemasSubsistemas(orderBy: $orderBy) { codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema } }",
  "variables": {
    "orderBy": "NOMBRE_SISTEMA_ASC"
  }
}
```

### 3.4. Solo códigos (para poblar filtros)

```json
{
  "query": "query { sistemasSubsistemas { codigo_sistema codigo_subsistema } }"
}
```

### 3.5. Ordenar por código de subsistema

```json
{
  "query": "query GruposPorSubsistema($orderBy: SistemaOrderBy) { sistemasSubsistemas(orderBy: $orderBy) { codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema } }",
  "variables": {
    "orderBy": "CODIGO_SUBSISTEMA_ASC"
  }
}
```

---

## 4. Casos de Uso Completos

### 4.1. Dashboard de productos por sistema

**Paso 1: Obtener catálogo de sistemas**
```json
{
  "query": "query { sistemasSubsistemas(orderBy: NOMBRE_SISTEMA_ASC) { codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema } }"
}
```

**Paso 2: Obtener productos activos del sistema seleccionado**
```json
{
  "query": "query ProductosActivos($filter: ProductoFilter) { productos(page: 1, pageSize: 100, filter: $filter) { data { codigo_producto nombre_producto codigo_subsistema nombre_subsistema } pagination { totalRegistros } } }",
  "variables": {
    "filter": {
      "codigo_sistema": "70",
      "estado": "ACTIVO"
    }
  }
}
```

**Paso 3: Obtener productos inactivos del mismo sistema**
```json
{
  "query": "query ProductosInactivos($filter: ProductoInactivoFilter) { productosInactivos(page: 1, pageSize: 100, filter: $filter) { data { codigo_producto nombre_producto fecha_actualizacion } pagination { totalRegistros } } }",
  "variables": {
    "filter": {
      "codigo_sistema": "70"
    }
  }
}
```

### 4.2. Búsqueda universal

**Buscar en activos**
```json
{
  "query": "query BuscarEnActivos($termino: String!) { productos(page: 1, pageSize: 50, filter: { nombre_producto_contains: $termino, estado: ACTIVO }) { data { codigo_producto nombre_producto estado } pagination { totalRegistros } } }",
  "variables": {
    "termino": "ACEITE"
  }
}
```

**Buscar en inactivos**
```json
{
  "query": "query BuscarEnInactivos($termino: String!) { productosInactivos(page: 1, pageSize: 50, filter: { nombre_producto_contains: $termino }) { data { codigo_producto nombre_producto estado } pagination { totalRegistros } } }",
  "variables": {
    "termino": "ACEITE"
  }
}
```

### 4.3. Reporte completo de un sistema

```json
{
  "query": "query ReporteSistema($codigoSistema: String!) { activos: productos(page: 1, pageSize: 1000, filter: { codigo_sistema: $codigoSistema, estado: ACTIVO }) { data { codigo_producto nombre_producto codigo_subsistema trabajo_repuesto } pagination { totalRegistros } } inactivos: productosInactivos(page: 1, pageSize: 1000, filter: { codigo_sistema: $codigoSistema }) { data { codigo_producto nombre_producto codigo_subsistema fecha_actualizacion } pagination { totalRegistros } } }",
  "variables": {
    "codigoSistema": "70"
  }
}
```

---

## 5. Ejemplos con cURL (PowerShell)

### 5.1. Listar sistemas y subsistemas

```powershell
$body = @{
  query = "query { sistemasSubsistemas { codigo_sistema nombre_sistema codigo_subsistema nombre_subsistema } }"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method POST `
  -Uri "https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql" `
  -Headers @{
    "x-api-key" = "da2-lagw6sktkbe5zca5zcqmw5e3oi"
    "Content-Type" = "application/json"
  } `
  -Body $body | ConvertTo-Json -Depth 5
```

### 5.2. Listar productos inactivos

```powershell
$body = @{
  query = "query { productosInactivos(page: 1, pageSize: 10) { data { codigo_producto nombre_producto estado } pagination { totalRegistros } } }"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method POST `
  -Uri "https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql" `
  -Headers @{
    "x-api-key" = "da2-lagw6sktkbe5zca5zcqmw5e3oi"
    "Content-Type" = "application/json"
  } `
  -Body $body | ConvertTo-Json -Depth 5
```

### 5.3. Productos por sistema

```powershell
$body = @{
  query = "query ProductosPorSistema(`$filter: ProductoFilter) { productos(page: 1, pageSize: 50, filter: `$filter) { data { codigo_producto nombre_producto } pagination { totalRegistros } } }"
  variables = @{
    filter = @{
      codigo_sistema = "70"
      estado = "ACTIVO"
    }
  }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Method POST `
  -Uri "https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql" `
  -Headers @{
    "x-api-key" = "da2-lagw6sktkbe5zca5zcqmw5e3oi"
    "Content-Type" = "application/json"
  } `
  -Body $body | ConvertTo-Json -Depth 5
```

---

## 6. Resumen de Queries Disponibles

| Query | Propósito | Paginación | Resultado |
|---|---|---|---|
| `productos` | Catálogo general con filtros | ✅ Sí | 10,126 activos |
| `productosInactivos` | Solo productos inactivos | ✅ Sí | 14 inactivos |
| `sistemasSubsistemas` | Grupos únicos sin duplicados | ❌ No | 43 combinaciones |

---

## 7. Notas Importantes

1. **sistemasSubsistemas NO requiere paginación**: Retorna todos los resultados de una vez (43 items)
2. **Todas las queries soportan selección flexible de campos**: Solo pide los campos que necesitas
3. **Los filtros son opcionales**: Puedes combinarlos según necesites
4. **Sin duplicados garantizado**: `sistemasSubsistemas` usa SELECT DISTINCT
5. **Formato consistente**: Todas las queries siguen el mismo patrón de variables

---

**Última actualización**: Octubre 2026  
**Versión**: 2.0  
**Estado**: ✅ Producción
