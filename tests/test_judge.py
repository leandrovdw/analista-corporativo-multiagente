"""
Tests del LLM-as-a-Judge.

Se prueban las partes puras (construcción de prompt y parseo del veredicto) y
la orquestación de `evaluar_respuesta` inyectando un cliente OpenAI falso, para
no hacer llamadas de red en los tests.
"""

from evaluations.judge import (
    construir_prompt_juez,
    parsear_veredicto,
    evaluar_respuesta,
)


# --- Cliente OpenAI falso para no llamar a la red ---------------------------

class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeCompletion:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content):
        self._content = content

    def create(self, **_kwargs):
        return _FakeCompletion(self._content)


class _FakeChat:
    def __init__(self, content):
        self.completions = _FakeCompletions(content)


class FakeOpenAI:
    def __init__(self, content):
        self.chat = _FakeChat(content)


# --- Tests de funciones puras -----------------------------------------------

def test_construir_prompt_incluye_todo():
    prompt = construir_prompt_juez(
        pregunta="¿VM vigente?",
        respuesta="Es $106.000",
        criterios=["Da un monto", "Cita el acta"],
    )
    assert "¿VM vigente?" in prompt
    assert "Es $106.000" in prompt
    assert "1. Da un monto" in prompt
    assert "2. Cita el acta" in prompt


def test_parsear_json_pelado():
    v = parsear_veredicto('{"veredicto": "PASS", "score": 8, "justificacion": "ok"}')
    assert v["veredicto"] == "PASS"
    assert v["score"] == 8


def test_parsear_json_en_bloque_markdown():
    texto = '```json\n{"veredicto":"FAIL","score":3,"justificacion":"falta acta"}\n```'
    v = parsear_veredicto(texto)
    assert v["veredicto"] == "FAIL"
    assert v["score"] == 3


def test_parsear_json_con_texto_alrededor():
    texto = 'Acá va mi evaluación: {"veredicto":"PASS","score":10} listo.'
    v = parsear_veredicto(texto)
    assert v["veredicto"] == "PASS"
    assert v["score"] == 10


def test_parsear_score_se_acota_a_rango():
    v = parsear_veredicto('{"veredicto":"PASS","score":99}')
    assert v["score"] == 10


def test_parsear_invalido_devuelve_fail():
    v = parsear_veredicto("esto no es json")
    assert v["veredicto"] == "FAIL"
    assert v["score"] == 0


# --- Test de evaluar_respuesta con cliente falso ----------------------------

def test_evaluar_respuesta_con_cliente_falso():
    fake = FakeOpenAI('{"veredicto":"PASS","score":9,"justificacion":"cumple"}')
    v = evaluar_respuesta(
        pregunta="¿VM vigente?",
        respuesta="El Valor Módulo vigente es $106.000 (Acta 360).",
        criterios=["Da un monto", "Cita el acta"],
        client=fake,
    )
    assert v["veredicto"] == "PASS"
    assert v["score"] == 9
