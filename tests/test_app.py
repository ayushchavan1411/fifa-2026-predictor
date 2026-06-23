import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from translations import translate

def test_translate_english():
    assert translate("Hello", "en") == "Hello"

def test_translate_hindi():
    result = translate("Hello", "hi")
    assert result == "Hello" or result == "हैलो"
