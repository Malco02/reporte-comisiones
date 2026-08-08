"""
etl.py
-------
Pipeline DataOps: calcula el salario total de los empleados combinando
la tabla rrhh.empleado (PostgreSQL) con el archivo de comisiones (CSV).

Uso:
    python src/etl.py --csv data/ComisionEmpleados_V1_202608.csv --out output/salario_total.parquet

Variables de entorno requeridas (ver .env.example):
    DB_HOST, DB_PORT, DB_NAME, DB_SCHEMA, DB_USER, DB_PASSWORD
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("etl")


def get_engine():
    """Crea el engine de conexión a PostgreSQL a partir de variables de entorno."""
    host = os.environ["DB_HOST"]
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ["DB_NAME"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=int(port),
        database=name,
    )
    return create_engine(url)


def extract_empleados(engine, schema: str = "rrhh") -> pd.DataFrame:
    """Extrae la tabla de empleados desde PostgreSQL."""
    query = f"""
        SELECT empleado_id, tip_documento, num_documento, nom_empleado,
               ape_empleado, cod_cargo, cod_departamento,
               mnt_salario, mnt_tope_comision
        FROM {schema}.empleado
    """
    logger.info("Extrayendo datos de %s.empleado ...", schema)
    df = pd.read_sql(query, engine)
    logger.info("Filas extraídas de PostgreSQL: %d", len(df))
    return df


def extract_comisiones(csv_path: str) -> pd.DataFrame:
    """Lee el archivo CSV de comisiones (separador ';')."""
    logger.info("Leyendo CSV de comisiones: %s", csv_path)
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
    df = df.rename(columns={"Comisión": "comision", "Nombre y Apellido": "nombre_apellido_csv"})
    logger.info("Filas leídas del CSV: %d", len(df))
    return df


def transform(df_empleado: pd.DataFrame, df_comision: pd.DataFrame, how: str = "left") -> pd.DataFrame:
    """
    Realiza el Join por empleado_id y calcula salario_total = mnt_salario + comision.

    how='left'  -> conserva a todos los empleados de la BD; comisión = 0 si no tiene registro en el CSV.
    how='inner' -> conserva solo empleados presentes en ambas fuentes.
    """
    df = df_empleado.merge(df_comision[["empleado_id", "comision"]], on="empleado_id", how=how)
    df["comision"] = df["comision"].fillna(0)
    df["salario_total"] = df["mnt_salario"].astype(float) + df["comision"].astype(float)

    logger.info(
        "Join (%s) completado: %d filas -> %d filas resultantes", how, len(df_empleado), len(df)
    )
    return df


def load(df: pd.DataFrame, out_path: str) -> None:
    """Guarda el resultado consolidado en formato Parquet."""
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_file, index=False)
    logger.info("Archivo Parquet generado en: %s (%d filas)", out_file, len(df))

    # Copia adicional en Excel, útil para revisión manual / evidencias
    excel_path = out_file.with_suffix(".xlsx")
    df.to_excel(excel_path, index=False)
    logger.info("Copia en Excel generada en: %s", excel_path)


def run(csv_path: str, out_path: str, join_how: str = "left") -> pd.DataFrame:
    engine = get_engine()
    df_empleado = extract_empleados(engine)
    df_comision = extract_comisiones(csv_path)
    df_result = transform(df_empleado, df_comision, how=join_how)
    load(df_result, out_path)
    return df_result


def parse_args():
    parser = argparse.ArgumentParser(description="ETL de comisiones de empleados")
    parser.add_argument("--csv", required=True, help="Ruta al archivo CSV de comisiones")
    parser.add_argument("--out", required=True, help="Ruta de salida del archivo Parquet")
    parser.add_argument(
        "--join-how", default="left", choices=["left", "inner"], help="Tipo de join (default: left)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run(args.csv, args.out, args.join_how)
    except Exception:
        logger.exception("El pipeline falló")
        sys.exit(1)
