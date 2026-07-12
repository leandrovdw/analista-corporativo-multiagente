"""
Archivo de configuración general del proyecto.

Acá centralizamos la lectura de variables de entorno.
La idea es no escribir claves ni configuraciones sensibles
directamente dentro de los agentes.
"""

import os
from dotenv import load_dotenv


# Carga las variables definidas en el archivo .env
load_dotenv()


# API Key de OpenAI.
# LiteLLM la usará internamente cuando invoquemos modelos openai/*
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def validar_configuracion_basica():
    """
    Valida que las variables mínimas para arrancar el proyecto estén cargadas.

    En esta primera etapa solamente necesitamos OPENAI_API_KEY.
    Más adelante agregaremos Qdrant y NeonDB.
    """
    if not OPENAI_API_KEY:
        raise ValueError(
            "Falta OPENAI_API_KEY en el archivo .env. "
            "Agregala antes de ejecutar el proyecto."
        )