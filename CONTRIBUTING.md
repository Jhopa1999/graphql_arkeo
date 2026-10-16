# Guía para continuar el desarrollo

Pasos para que un desarrollador clone el proyecto y empiece a trabajar.

---

## 1. Requisitos

Instalar en la máquina de desarrollo:

- **Python 3.12** (runtime de la Lambda)
- **AWS CLI v2** — `aws --version`
- **AWS SAM CLI** — `sam --version`
- **Git**

---

## 2. Clonar el repositorio

```powershell
git clone https://github.com/Jhopa1999/graphql_arkeo.git
cd graphql_arkeo
```

---

## 3. Configurar credenciales AWS

El proyecto se despliega en la cuenta **481133585213**, región **us-east-2**.
El desarrollador necesita credenciales de esa cuenta con permisos para
CloudFormation, Lambda, AppSync, IAM, Secrets Manager y EC2 (VPC).

```powershell
aws configure
# Region: us-east-2
aws sts get-caller-identity   # verifica que apunta a la cuenta correcta
```

> Las credenciales AWS NO están en el repo (nunca deben estarlo). Cada dev usa
> las suyas.

---

## 4. Entorno Python y pruebas

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r src/requirements.txt
.\.venv\Scripts\python.exe -m pip install pytest boto3

# Pruebas unitarias (no requieren AWS ni base de datos)
.\.venv\Scripts\python.exe -m pytest -q
```

### Pruebas de integración (opcionales)

Requieren red hacia SQL Server (VPN) y acceso al secret:

```powershell
$env:RUN_DB_INTEGRATION="1"; $env:AWS_REGION="us-east-2"
.\.venv\Scripts\python.exe -m pytest tests/test_integration.py -q
```

Prueba end-to-end contra el endpoint (tras desplegar):

```powershell
$env:APPSYNC_API_KEY="<api-key-vigente>"
.\.venv\Scripts\python.exe scripts\prueba_graphql.py
```

El API key se obtiene así (no se versiona):

```powershell
aws appsync list-api-keys --api-id ufhb53oaaras3pugztjg5ektqu --region us-east-2
```

---

## 5. Desplegar cambios

```powershell
sam build
sam deploy
```

Los parámetros por defecto en `samconfig.toml` ya apuntan a los recursos
existentes (VPC, subnets, security group y secret). No es necesario pasarlos a
mano.

---

## 6. Flujo de trabajo con Git

No trabajar directo sobre `main`. Usar ramas:

```powershell
git checkout -b feature/mi-cambio
# ... editar código ...
.\.venv\Scripts\python.exe -m pytest -q      # que pasen las pruebas
git add <archivos>
git commit -m "feat: descripcion del cambio"
git push -u origin feature/mi-cambio
```

Luego abrir un **Pull Request** en GitHub hacia `main` para revisión.

---

## 7. Estructura del proyecto

```
graphql_arkeo/
├── template.yaml              # Infraestructura SAM/CloudFormation
├── samconfig.toml             # Parámetros de despliegue (us-east-2)
├── schema.graphql             # Esquema GraphQL de AppSync
├── resolvers/                 # Plantillas VTL del resolver
├── src/                       # Código Lambda (raíz del paquete desplegado)
│   ├── handler.py             # Entry point AppSync + paginación
│   ├── config.py              # Credenciales (Secrets Manager) y límites
│   ├── query_builder.py       # SQL parametrizado (reglas + filtros)
│   ├── database.py            # Conexión pytds y ejecución
│   └── requirements.txt       # Dependencias de la Lambda
├── tests/                     # Pruebas unitarias e integración
├── scripts/                   # Scripts de prueba manual
├── README.md                  # Guía técnica general
├── ENTREGA_API.md             # Documento de entrega del proyecto
├── GUIA_DESARROLLADOR.md      # Guía para quien CONSUME el API
└── CONTRIBUTING.md            # Este archivo
```

---

## 8. Dónde cambiar cada cosa

| Quiero... | Archivo |
|---|---|
| Agregar/quitar un campo del API | `schema.graphql` + `src/query_builder.py` (SELECT) |
| Agregar un filtro nuevo | `schema.graphql` (input) + `src/query_builder.py` |
| Cambiar la lógica de paginación | `src/handler.py` + `src/query_builder.py` |
| Agregar una query nueva | `schema.graphql` + resolver en `resolvers/` + `src/handler.py` + `template.yaml` |
| Cambiar límites de página / memoria / timeout | `template.yaml` (Parameters / Globals) |
| Cambiar la conexión a base de datos | `src/database.py` |

Tras cualquier cambio: correr `pytest`, luego `sam build` y `sam deploy`.

---

## 9. Notas importantes

- **Nunca** subir credenciales, API keys ni archivos `.env` al repo.
- Las credenciales de SQL Server viven en el secret `seven-db-credentials`
  (Secrets Manager); el código las lee en runtime, no se hardcodean.
- La Lambda corre en VPC y alcanza SQL Server (`10.125.18.16`) por VPN. Para
  probar contra la base desde local, el dev necesita estar en la VPN.
- Las consultas SQL son 100% parametrizadas: mantener ese patrón al editar
  `query_builder.py` (no concatenar valores de usuario).
