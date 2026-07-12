"""
Tests de la tool determinística de cálculo de Valores Módulo.

Al ser matemática pura, se prueba sin servicios externos ni LLM.
"""

import pytest

from app.tools.calculo_tools import calcular_cantidad_modulos


def test_calculo_basico():
    resultado = calcular_cantidad_modulos(monto_compra=15_000_000, valor_modulo=106_000)
    assert resultado["ok"] is True
    # 15.000.000 / 106.000 = 141,50943... -> redondea a 141,51
    assert resultado["cantidad_vm"] == pytest.approx(141.51, abs=0.01)


def test_calculo_exacto():
    resultado = calcular_cantidad_modulos(monto_compra=1_060_000, valor_modulo=106_000)
    assert resultado["cantidad_vm"] == pytest.approx(10.0, abs=0.001)


def test_monto_invalido():
    with pytest.raises(ValueError):
        calcular_cantidad_modulos(monto_compra=0, valor_modulo=106_000)


def test_valor_modulo_invalido():
    with pytest.raises(ValueError):
        calcular_cantidad_modulos(monto_compra=15_000_000, valor_modulo=0)
