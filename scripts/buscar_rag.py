"""
Script de prueba para búsqueda semántica.

Este archivo usa app.rag.client.buscar_chunks().
No contiene lógica propia de OpenAI ni Qdrant.
Uso de pruebas
"""

from app.rag.client import buscar_chunks


def imprimir_resultados(pregunta: str, resultados: list[dict]):
    print("=" * 80)
    print("BÚSQUEDA SEMÁNTICA RAG")
    print("=" * 80)
    print("\nPregunta:")
    print(pregunta)

    if not resultados:
        print("\nNo se encontraron resultados con score suficiente.")
        return

    print("\nResultados recuperados:")

    for i, resultado in enumerate(resultados, start=1):
        print("\n" + "-" * 80)
        print(f"Resultado #{i}")
        print(f"Score: {resultado['score']}")
        print(f"Fuente: {resultado['source']}")
        print(f"Chunk: {resultado['chunk']}")
        print("-" * 80)
        print(resultado["text"][:1200])


def main():
    preguntas = [
        "¿Qué es el Valor Módulo?",
        "¿Qué procedimiento corresponde para más de 100 VM y hasta 500 VM?",
        "¿Dónde debe consultarse el valor módulo vigente?",
        "¿Está permitido fraccionar una contratación para evitar una licitación?",
    ]

    for pregunta in preguntas:
        resultados = buscar_chunks(
            pregunta=pregunta,
            top_k=2,
            score_minimo=0.50,
        )

        imprimir_resultados(pregunta, resultados)


if __name__ == "__main__":
    main()