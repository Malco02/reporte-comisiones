"""
Tests unitarios del pipeline. No requieren conexión a PostgreSQL:
se prueba la función `transform`, que es la lógica de negocio central
(join + cálculo de salario_total).
"""

import pandas as pd
import pytest

from src.etl import transform


@pytest.fixture
def df_empleado():
    return pd.DataFrame(
        {
            "empleado_id": [1, 2, 3],
            "nom_empleado": ["Juan", "Maria", "Carlos"],
            "ape_empleado": ["Perez", "Gomez", "Martinez"],
            "mnt_salario": [3000.0, 3500.0, 4000.0],
        }
    )


@pytest.fixture
def df_comision():
    return pd.DataFrame(
        {
            "empleado_id": [1, 2],  # empleado 3 no tiene comisión en el CSV
            "comision": [9000, 8250],
        }
    )


def test_salario_total_se_calcula_correctamente(df_empleado, df_comision):
    result = transform(df_empleado, df_comision, how="left")
    fila_1 = result.loc[result["empleado_id"] == 1, "salario_total"].iloc[0]
    assert fila_1 == 3000.0 + 9000


def test_left_join_conserva_empleados_sin_comision(df_empleado, df_comision):
    result = transform(df_empleado, df_comision, how="left")
    assert len(result) == 3
    fila_3 = result.loc[result["empleado_id"] == 3]
    assert fila_3["comision"].iloc[0] == 0
    assert fila_3["salario_total"].iloc[0] == 4000.0


def test_inner_join_descarta_empleados_sin_comision(df_empleado, df_comision):
    result = transform(df_empleado, df_comision, how="inner")
    assert len(result) == 2
    assert set(result["empleado_id"]) == {1, 2}


def test_no_hay_valores_nulos_en_salario_total(df_empleado, df_comision):
    result = transform(df_empleado, df_comision, how="left")
    assert result["salario_total"].isnull().sum() == 0
