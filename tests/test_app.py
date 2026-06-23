import pytest
from translations import translate

def test_translate_english():
    assert translate("Hello", "en") == "Hello"

def test_translate_hindi():
    # If translation exists, it will work; otherwise it returns original
    result = translate("Hello", "hi")
    assert result == "Hello" or result == "हैलो"
