"""
Tools RAG para ser usadas por agentes ADK.

Esta tool encapsula la búsqueda semántica en Qdrant.
El agente no necesita saber cómo funciona Qdrant ni OpenAI embeddings:
simplemente llama a esta función con una pregunta.
"""

from app.rag.client import buscar_chunks


def consultar_documentacion_corporativa(pregunta: str) -> dict:
    """
    Consulta la documentación corporativa de PALERMIA S.A. usando RAG.

    Parámetros:
    - pregunta: consulta formulada por el agente.

    Devuelve:
    - fragmentos relevantes encontrados en Qdrant.
    - fuentes documentales.
    """

    chunks = buscar_chunks(
        pregunta=pregunta,
        top_k=4,
        score_minimo=0.45,
    )

    if not chunks:
        return {
            "ok": False,
            "mensaje": "No se encontraron fragmentos relevantes en la documentación corporativa.",
            "resultados": [],
        }

    return {
        "ok": True,
        "mensaje": "Se encontraron fragmentos relevantes en la documentación corporativa.",
        "resultados": chunks,
    }