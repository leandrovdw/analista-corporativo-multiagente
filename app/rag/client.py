"""
Cliente reutilizable para RAG con Qdrant + OpenAI.

Este archivo centraliza:
- conexión a OpenAI;
- conexión a Qdrant;
- creación de embeddings;
- búsqueda semántica.

Así evitamos repetir código en:
- ingest.py
- search.py
- futuras tools del agente RAG
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient


load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "palermia_docs")

OPENAI_EMBEDDING_MODEL = os.getenv(
    "OPENAI_EMBEDDING_MODEL",
    "text-embedding-3-small",
)


def validar_configuracion_rag():
    """
    Valida que estén cargadas las variables necesarias para RAG.
    """

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Falta OPENAI_API_KEY en .env")

    if not QDRANT_URL:
        raise ValueError("Falta QDRANT_URL en .env")

    if not QDRANT_API_KEY:
        raise ValueError("Falta QDRANT_API_KEY en .env")


@lru_cache(maxsize=1)
def obtener_cliente_openai() -> OpenAI:
    """
    Crea (y cachea) el cliente OpenAI.

    Se cachea para no reinstanciar el cliente en cada embedding
    durante la ingesta de documentos.
    """

    validar_configuracion_rag()
    return OpenAI()


@lru_cache(maxsize=1)
def obtener_cliente_qdrant() -> QdrantClient:
    """
    Crea (y cachea) el cliente Qdrant.
    """

    validar_configuracion_rag()

    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        check_compatibility=False,
    )


def crear_embedding(texto: str) -> list[float]:
    """
    Genera un embedding para un texto usando OpenAI.

    Este método se usa tanto para:
    - ingestar chunks;
    - buscar por similitud semántica.
    """

    client = obtener_cliente_openai()

    response = client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=texto,
    )

    return response.data[0].embedding


def buscar_chunks(
    pregunta: str,
    top_k: int = 2,
    score_minimo: float = 0.50,
) -> list[dict]:
    """
    Busca chunks relevantes en Qdrant.

    Devuelve una lista de diccionarios simples para que luego
    puedan ser usados por agentes o impresos en consola.

    Parámetros:
    - pregunta: consulta del usuario.
    - top_k: cantidad máxima de chunks a recuperar.
    - score_minimo: umbral mínimo de similitud.
    """

    qdrant_client = obtener_cliente_qdrant()
    vector = crear_embedding(pregunta)

    response = qdrant_client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=vector,
        limit=top_k,
    )

    chunks = []

    for point in response.points:
        if point.score < score_minimo:
            continue

        payload = point.payload or {}

        chunks.append(
            {
                "score": point.score,
                "text": payload.get("text", ""),
                "source": payload.get("source", "sin fuente"),
                "chunk": payload.get("chunk", None),
                "extension": payload.get("extension", None),
            }
        )

    return chunks