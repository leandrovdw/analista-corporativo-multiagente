"""
Herramientas determinísticas para cálculos del proceso de compras.

Estas operaciones no requieren un LLM:
- son matemáticas;
- deben ser exactas;
- deben poder probarse de manera aislada.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def calcular_cantidad_modulos(
    monto_compra: float,
    valor_modulo: float,
) -> dict:
    """
    Calcula cuántos Valores Módulo representa una contratación.

    Fórmula:
        cantidad_vm = monto_compra / valor_modulo

    Args:
        monto_compra:
            Monto estimado de la compra expresado en pesos.

        valor_modulo:
            Valor monetario vigente de una unidad de Valor Módulo.

    Returns:
        Diccionario estructurado con monto, VM y resultado.

    Raises:
        ValueError:
            Cuando los valores son inválidos, negativos o cero.
    """

    try:
        monto = Decimal(str(monto_compra))
        modulo = Decimal(str(valor_modulo))
    except InvalidOperation as exc:
        raise ValueError(
            "El monto de compra y el Valor Módulo deben ser numéricos."
        ) from exc

    if monto <= 0:
        raise ValueError("El monto de compra debe ser mayor que cero.")

    if modulo <= 0:
        raise ValueError("El Valor Módulo debe ser mayor que cero.")

    cantidad_vm = monto / modulo

    # Redondeamos solamente para presentación.
    cantidad_vm_redondeada = cantidad_vm.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return {
        "ok": True,
        "monto_compra": float(monto),
        "valor_modulo": float(modulo),
        "cantidad_vm": float(cantidad_vm_redondeada),
        "formula": (
            f"{float(monto):.2f} / "
            f"{float(modulo):.2f} = "
            f"{float(cantidad_vm_redondeada):.2f} VM"
        ),
    }