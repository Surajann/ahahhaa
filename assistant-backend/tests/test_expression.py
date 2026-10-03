from anime_assistant.core.expression import parse_expression


def test_expression_parse_happy():
    cleaned, expr = parse_expression("Halo ne~ [happy]")
    assert cleaned == "Halo ne~"
    assert expr == "happy"


def test_expression_parse_no_tag():
    cleaned, expr = parse_expression("Tanpa tag")
    assert cleaned == "Tanpa tag"
    assert expr == "idle"


def test_expression_parse_thinking():
    cleaned, expr = parse_expression("Eto... [thinking]")
    assert cleaned == "Eto..."
    assert expr == "thinking"
