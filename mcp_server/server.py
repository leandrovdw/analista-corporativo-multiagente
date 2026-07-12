import os

from dotenv import load_dotenv
from fastmcp import FastMCP
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Falta DATABASE_URL en .env")

engine = create_engine(DATABASE_URL)

mcp = FastMCP("mcp-palermia-compras")


@mcp.tool()
def consultar_valor_modulo() -> str:
    """
    Consulta el Valor Módulo vigente de PALERMIA S.A.
    """

    sql = text("""
        SELECT valor, acta_directorio, fecha_desde
        FROM valores_modulo
        WHERE vigente = TRUE
        ORDER BY fecha_desde DESC
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(sql).fetchone()

    if not row:
        return "No se encontró un Valor Módulo vigente."

    return (
        f"Valor Módulo vigente: ${float(row.valor):,.2f}\n"
        f"Acta de Directorio: {row.acta_directorio}\n"
        f"Fecha de vigencia: {row.fecha_desde}"
    )


@mcp.tool()
def buscar_empleado_por_cargo(cargo: str) -> str:
    """
    Busca empleados activos de PALERMIA S.A. por cargo.
    """

    sql = text("""
        SELECT legajo, nombre, apellido, cargo, gerencia, email
        FROM empleados
        WHERE activo = TRUE
          AND lower(cargo) = lower(:cargo)
        ORDER BY apellido, nombre
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, {"cargo": cargo}).fetchall()

    if not rows:
        return f"No se encontraron empleados activos con cargo: {cargo}"

    salida = []

    for row in rows:
        salida.append(
            f"Legajo: {row.legajo}\n"
            f"Nombre: {row.nombre} {row.apellido}\n"
            f"Cargo: {row.cargo}\n"
            f"Gerencia: {row.gerencia}\n"
            f"Email: {row.email}"
        )

    return "\n\n".join(salida)


@mcp.tool()
def listar_valores_modulo() -> str:
    """
    Lista el historial de Valores Módulo.
    """

    sql = text("""
        SELECT fecha_desde, fecha_hasta, valor, acta_directorio, vigente
        FROM valores_modulo
        ORDER BY fecha_desde DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql).fetchall()

    if not rows:
        return "No hay valores módulo cargados."

    salida = []

    for row in rows:
        hasta = row.fecha_hasta if row.fecha_hasta else "vigente"
        estado = "VIGENTE" if row.vigente else "histórico"

        salida.append(
            f"Desde: {row.fecha_desde} | Hasta: {hasta} | "
            f"Valor: ${float(row.valor):,.2f} | "
            f"Acta: {row.acta_directorio} | Estado: {estado}"
        )

    return "\n".join(salida)


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8001,
        path="/mcp",
    )