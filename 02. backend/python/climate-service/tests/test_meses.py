import pytest

from app.meses import parse_mes, parse_meses


@pytest.mark.parametrize(
    "valor, mes",
    [(9, 9), ("9", 9), ("sep", 9), ("Septiembre", 9), ("setiembre", 9), ("Ago", 8), ("dic", 12), ("Enero", 1)],
)
def test_parse_mes(valor, mes):
    assert parse_mes(valor) == mes


@pytest.mark.parametrize("malo", [0, 13, "xyz", True, ""])
def test_parse_mes_invalido(malo):
    with pytest.raises(ValueError):
        parse_mes(malo)


def test_parse_meses_ordena_y_quita_repetidos():
    assert parse_meses(["dic", 1, "ene", 11]) == [1, 11, 12]
    assert parse_meses(None) == []
    assert parse_meses("mar") == [3]
