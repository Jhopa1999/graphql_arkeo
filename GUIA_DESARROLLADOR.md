# Guía de integración — API GraphQL ARKEO Fleet (Catálogo de productos)

Guía para desarrolladores que van a **consumir** el API. Explica cómo conectarse,
qué consultar, cómo paginar y filtrar, y cómo manejar errores. No requiere
conocer la infraestructura detrás.

---

## 1. Lo mínimo para empezar

| Dato | Valor |
|---|---|
| **URL** | `https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql` |
| **Método** | `POST` |
| **Header 1** | `Content-Type: application/json` |
| **Header 2** | `x-api-key: <TU_API_KEY>` |

Es una API **GraphQL**. Siempre se llama con `POST` y el cuerpo es un JSON con
el campo `query` (y opcionalmente `variables`).

Prueba rápida (una línea):

```bash
curl -s -X POST "https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql" \
  -H "Content-Type: application/json" \
  -H "x-api-key: <TU_API_KEY>" \
  -d '{"query":"query { productos(page:1, pageSize:5) { data { codigo_producto nombre_producto } pagination { totalRegistros } } }"}'
```

---

## 2. La única operación: `productos`

```graphql
productos(
  page: Int = 1
  pageSize: Int = 100
  filter: ProductoFilter
  orderBy: ProductoOrderBy = CODIGO_PRODUCTO_ASC
): ProductoConnection!
```

Devuelve un objeto con dos partes:

- `data`: la lista de productos de la página pedida.
- `pagination`: los metadatos para saber cuántas páginas hay y si seguir.

> En GraphQL **tú eliges qué campos recibir**. Pide solo lo que necesitas: la
> respuesta trae exactamente esos campos, ni más ni menos.

### Campos de un producto

| Campo | Tipo | Descripción |
|---|---|---|
| `codigo_producto` | String | Código único del producto |
| `nombre_producto` | String | Nombre/descripción |
| `codigo_tipo` | String | Código del tipo |
| `nombre_tipo` | String | Nombre del tipo |
| `estado` | String | `ACTIVO` o `INACTIVO` |
| `codigo_sistema` | String | Código de sistema |
| `nombre_sistema` | String | Nombre de sistema |
| `codigo_subsistema` | String | Código de subsistema |
| `nombre_subsistema` | String | Nombre de subsistema |
| `fecha_creacion` | String | Fecha ISO 8601 (`2018-06-06T18:47:55.377`) |
| `fecha_actualizacion` | String | Fecha ISO 8601 |
| `codigo_unidad` | String | Código de unidad de medida |
| `nombre_unidad` | String | Nombre de unidad (ej. `UNIDAD`) |
| `trabajo_repuesto` | String | `TRABAJO` o `REPUESTO` |

### Campos de paginación

| Campo | Tipo | Descripción |
|---|---|---|
| `page` | Int | Página actual (empieza en 1) |
| `pageSize` | Int | Tamaño de página aplicado |
| `totalRegistros` | Int | Total de registros que cumplen la consulta |
| `totalPaginas` | Int | Total de páginas |
| `hasNextPage` | Boolean | ¿Hay página siguiente? |
| `hasPreviousPage` | Boolean | ¿Hay página anterior? |

---

## 3. Paginación

- `page` empieza en **1**.
- `pageSize` por defecto **100**, máximo **1000**. Si pides más, se ajusta a 1000.
- Para recorrer todo: empieza en `page: 1` y sigue incrementando mientras
  `pagination.hasNextPage` sea `true`.

```graphql
query {
  productos(page: 1, pageSize: 50) {
    data { codigo_producto }
    pagination { page totalPaginas hasNextPage }
  }
}
```

---

## 4. Filtros

Todos opcionales. Si envías varios, se combinan con **AND** (deben cumplirse todos).

| Filtro | Tipo | Comportamiento |
|---|---|---|
| `codigo_producto` | String | Coincidencia **exacta** |
| `codigo_producto_contains` | String | Coincidencia **parcial** (contiene) |
| `nombre_producto_contains` | String | Coincidencia **parcial** (contiene) |
| `codigo_tipo` | String | Exacta |
| `estado` | `ACTIVO` / `INACTIVO` | Exacta |
| `codigo_sistema` | String | Exacta |
| `codigo_subsistema` | String | Exacta |
| `codigo_unidad` | String | Exacta |
| `trabajo_repuesto` | `TRABAJO` / `REPUESTO` | Exacta |

> `estado` y `trabajo_repuesto` son **enums**: se escriben sin comillas en la
> query (ej. `estado: ACTIVO`), o como string en las variables (ej. `"ACTIVO"`).

Ejemplo:

```graphql
query {
  productos(
    page: 1
    pageSize: 20
    filter: { estado: ACTIVO, trabajo_repuesto: REPUESTO, nombre_producto_contains: "ACEITE" }
  ) {
    data { codigo_producto nombre_producto }
    pagination { totalRegistros }
  }
}
```

---

## 5. Ordenamiento

Valor de `orderBy` (opcional, por defecto `CODIGO_PRODUCTO_ASC`):

`CODIGO_PRODUCTO_ASC`, `CODIGO_PRODUCTO_DESC`,
`NOMBRE_PRODUCTO_ASC`, `NOMBRE_PRODUCTO_DESC`,
`FECHA_CREACION_ASC`, `FECHA_CREACION_DESC`.

El orden es estable entre páginas (desempata siempre por `codigo_producto`).

---

## 6. Usar variables (recomendado)

En lugar de concatenar valores en el texto de la query, usa variables. Es más
seguro y legible:

**Query:**
```graphql
query ListarProductos($page: Int!, $size: Int!, $filter: ProductoFilter, $order: ProductoOrderBy) {
  productos(page: $page, pageSize: $size, filter: $filter, orderBy: $order) {
    data {
      codigo_producto
      nombre_producto
      estado
      trabajo_repuesto
    }
    pagination {
      page
      totalRegistros
      totalPaginas
      hasNextPage
    }
  }
}
```

**Variables:**
```json
{
  "page": 1,
  "size": 50,
  "filter": { "estado": "ACTIVO" },
  "order": "NOMBRE_PRODUCTO_ASC"
}
```

---

## 7. Formato de la respuesta

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
        "hasNextPage": true
      }
    }
  }
}
```

---

## 8. Manejo de errores

GraphQL **siempre responde HTTP 200** cuando la petición llega bien, incluso si
hay un error de negocio. El error viene en un arreglo `errors`:

```json
{
  "data": null,
  "errors": [
    { "message": "Error interno al consultar el catálogo de productos.", "errorType": "Lambda:Unhandled" }
  ]
}
```

**Regla práctica para el cliente:**
1. Si la respuesta trae `errors` → tratarlo como fallo, sin importar el HTTP 200.
2. Usar `data.productos` solo si `errors` no existe.

Códigos HTTP que sí verás:

| HTTP | Causa | Acción |
|---|---|---|
| 200 | OK (revisar `errors` igual) | Normal |
| 401 | Falta o es inválido el `x-api-key` | Revisar el header |
| 400 | Query mal formada | Revisar sintaxis GraphQL |

---

## 9. Ejemplos de código

### JavaScript / Node.js (fetch)

```javascript
const URL = "https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql";
const API_KEY = "<TU_API_KEY>";

const query = `
  query ($page: Int!, $size: Int!, $filter: ProductoFilter) {
    productos(page: $page, pageSize: $size, filter: $filter) {
      data { codigo_producto nombre_producto estado }
      pagination { totalRegistros totalPaginas hasNextPage }
    }
  }`;

async function listarProductos() {
  const resp = await fetch(URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": API_KEY },
    body: JSON.stringify({
      query,
      variables: { page: 1, size: 50, filter: { estado: "ACTIVO" } },
    }),
  });
  const json = await resp.json();
  if (json.errors) throw new Error(json.errors[0].message);
  return json.data.productos;
}

listarProductos().then((r) => console.log(r.pagination, r.data.length));
```

### Recorrer TODAS las páginas (Node.js)

```javascript
async function obtenerTodo(filter = null) {
  const todos = [];
  let page = 1;
  while (true) {
    const resp = await fetch(URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-api-key": API_KEY },
      body: JSON.stringify({
        query: `query ($p:Int!,$s:Int!,$f:ProductoFilter){
          productos(page:$p,pageSize:$s,filter:$f){
            data { codigo_producto nombre_producto }
            pagination { hasNextPage }
          }
        }`,
        variables: { p: page, s: 500, f: filter },
      }),
    });
    const json = await resp.json();
    if (json.errors) throw new Error(json.errors[0].message);
    const prod = json.data.productos;
    todos.push(...prod.data);
    if (!prod.pagination.hasNextPage) break;
    page++;
  }
  return todos;
}
```

### Python (requests)

```python
import requests

URL = "https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql"
API_KEY = "<TU_API_KEY>"

query = """
query ($page: Int!, $size: Int!, $filter: ProductoFilter) {
  productos(page: $page, pageSize: $size, filter: $filter) {
    data { codigo_producto nombre_producto estado }
    pagination { totalRegistros totalPaginas hasNextPage }
  }
}
"""

resp = requests.post(
    URL,
    headers={"Content-Type": "application/json", "x-api-key": API_KEY},
    json={"query": query, "variables": {"page": 1, "size": 50, "filter": {"estado": "ACTIVO"}}},
    timeout=40,
)
payload = resp.json()
if "errors" in payload:
    raise RuntimeError(payload["errors"][0]["message"])

productos = payload["data"]["productos"]
print(productos["pagination"]["totalRegistros"], "registros")
for p in productos["data"]:
    print(p["codigo_producto"], p["nombre_producto"])
```

### C# (.NET, HttpClient)

```csharp
using System.Net.Http;
using System.Text;
using System.Text.Json;

var url = "https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql";
var apiKey = "<TU_API_KEY>";

var body = new {
    query = @"query ($page:Int!, $size:Int!, $filter:ProductoFilter) {
        productos(page:$page, pageSize:$size, filter:$filter) {
            data { codigo_producto nombre_producto estado }
            pagination { totalRegistros totalPaginas hasNextPage }
        }
    }",
    variables = new { page = 1, size = 50, filter = new { estado = "ACTIVO" } }
};

using var client = new HttpClient();
client.DefaultRequestHeaders.Add("x-api-key", apiKey);
var content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
var resp = await client.PostAsync(url, content);
var json = await resp.Content.ReadAsStringAsync();
Console.WriteLine(json);
```

---

## 10. Probar sin escribir código

1. Importa `postman_collection.json` en Postman (incluye URL y API key ya cargados).
2. Ejecuta cualquiera de las requests de ejemplo.

O usa el editor **Consultas** de la consola de AWS AppSync con el mismo esquema.

---

## 11. Preguntas frecuentes

**¿Por qué GraphQL siempre devuelve 200 aunque falle?**
Es el comportamiento estándar de GraphQL. Revisa siempre el campo `errors`.

**¿Puedo pedir solo un campo?**
Sí. Pide exactamente los campos que uses; la respuesta no incluirá el resto.

**¿Hay límite de registros totales?**
No. El límite es por página (`pageSize` máx 1000). Recorre todo paginando.

**¿Cómo sé cuántas páginas hay?**
En `pagination.totalPaginas`, o avanza mientras `hasNextPage` sea `true`.

**El `x-api-key` tiene vencimiento.**
Sí, es una key de prueba. Si te da 401, solicita una key vigente al equipo que
administra el API.
