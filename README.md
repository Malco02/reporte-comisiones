# DataOps - Cálculo de Comisiones de Empleados

Pipeline que calcula el salario total de los empleados combinando:
- Tabla `rrhh.empleado` en PostgreSQL (host `mgg.vps.webdock.cloud`).
- Archivo CSV de comisiones (`ComisionEmpleados_V1_202608.csv`).

`salario_total = mnt_salario (PostgreSQL) + comision (CSV)`

Salida: archivo **Parquet** (y copia en Excel) con la tabla consolidada.

## Estructura del repositorio

```
.
├── src/
│   └── etl.py              # Extract - Transform - Load
├── tests/
│   └── test_etl.py         # Tests unitarios de la lógica de join/cálculo
├── data/
│   └── ComisionEmpleados_V1_202608.csv
├── output/                 # Resultados generados (parquet/xlsx) - no versionado
├── requirements.txt
├── .env.example             # Plantilla de variables de conexión
├── azure-pipelines.yml      # Pipeline CI/CD de Azure DevOps
└── README.md
```

## Cómo correrlo localmente

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Completar DB_PASSWORD en .env (no se sube al repo)
export $(cat .env | xargs)       # Windows: usar setx o cargar manualmente

python src/etl.py --csv data/ComisionEmpleados_V1_202608.csv --out output/salario_total.parquet
```

Esto genera `output/salario_total.parquet` y `output/salario_total.xlsx`.

## Tests

```bash
pytest tests/ -v
```

Los tests validan la lógica de negocio (join + cálculo de `salario_total`) con
datos simulados, sin necesidad de conexión real a la base de datos — así el
pipeline de CI puede ejecutarlos sin exponer credenciales.

## Despliegue en Azure DevOps (CI/CD)

1. **Crear el proyecto y subir el repo** a Azure DevOps (o vincular este repo de GitHub).
2. **Configurar Variable Groups** (Pipelines → Library):
   - `dataops-dev`: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (secreta).
   - `dataops-prod`: mismas variables para el entorno de producción.
3. **Crear los Environments** (Pipelines → Environments): `dev` y `production`.
   - En `production`, agregar un **Approval** (aprobación manual) para simular
     el control de despliegue antes de pasar a producción.
4. **Crear el pipeline** apuntando a `azure-pipelines.yml`.
5. Al hacer push a `main`, el pipeline corre automáticamente:
   - **Stage CI**: instala dependencias y corre los tests unitarios.
   - **Stage CD_Dev**: ejecuta el ETL real contra el entorno `dev`.
   - **Stage CD_Prod**: ejecuta el ETL real contra `production`, previa aprobación manual.

## Evidencias a capturar para el informe

- Captura del pipeline corriendo en Azure DevOps con las 3 etapas en verde.
- Captura del archivo Parquet/Excel generado (con conteo de filas).
- Captura del log de tests (`pytest`) pasando.
- Captura de la aprobación manual en el stage de producción.

## Notas de diseño

- El join es tipo `LEFT` por defecto (`--join-how left`): se conservan todos
  los empleados de PostgreSQL, y si no tienen comisión en el CSV se les asigna 0.
  Puede cambiarse a `inner` para conservar solo empleados presentes en ambas fuentes.
- Las credenciales de base de datos nunca se hardcodean: se leen de variables
  de entorno / Variable Groups secretos de Azure DevOps.
