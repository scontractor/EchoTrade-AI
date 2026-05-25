import pytest

from app.signals.analyst import _parse_response


def test_clean_json():
    raw = '{"executive_summary": "Strong conviction buys.", "signals": []}'
    result = _parse_response(raw)
    assert result["executive_summary"] == "Strong conviction buys."
    assert result["signals"] == []


def test_json_in_markdown_fences():
    raw = '```json\n{"executive_summary": "Rotation into tech.", "signals": []}\n```'
    result = _parse_response(raw)
    assert result["executive_summary"] == "Rotation into tech."


def test_json_in_plain_fences():
    raw = '```\n{"key": "value"}\n```'
    result = _parse_response(raw)
    assert result["key"] == "value"


def test_json_with_surrounding_prose():
    raw = 'Here is the analysis:\n{"key": "value"}\nHope that helps!'
    result = _parse_response(raw)
    assert result["key"] == "value"


def test_garbage_raises_value_error():
    with pytest.raises(ValueError, match="No JSON object found"):
        _parse_response("Sorry, I cannot provide investment advice.")


def test_empty_raises_value_error():
    with pytest.raises(ValueError):
        _parse_response("")
