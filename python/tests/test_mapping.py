"""Unit tests for the pure key-formatting helpers (no hardware needed)."""

from mapping import format_key


def test_plain_letters_are_lowercase():
    assert format_key("KEY_A") == "a"
    assert format_key("KEY_Z") == "z"


def test_shift_uppercases_letters():
    assert format_key("KEY_A", shift=True) == "A"


def test_caps_lock_uppercases_letters():
    assert format_key("KEY_A", caps=True) == "A"


def test_caps_lock_plus_shift_lowercases():
    # Both flags together cancel back out — classic US keyboard behaviour.
    assert format_key("KEY_A", shift=True, caps=True) == "a"


def test_digits_and_shift_symbols():
    assert format_key("KEY_1") == "1"
    assert format_key("KEY_1", shift=True) == "!"
    assert format_key("KEY_5", shift=True) == "%"
    assert format_key("KEY_0", shift=True) == ")"


def test_punctuation_with_and_without_shift():
    assert format_key("KEY_MINUS") == "-"
    assert format_key("KEY_MINUS", shift=True) == "_"
    assert format_key("KEY_SEMICOLON") == ";"
    assert format_key("KEY_SEMICOLON", shift=True) == ":"
    assert format_key("KEY_SLASH", shift=True) == "?"
    assert format_key("KEY_LEFTBRACE") == "["
    assert format_key("KEY_LEFTBRACE", shift=True) == "{"
    assert format_key("KEY_APOSTROPHE", shift=True) == '"'


def test_whitespace_keys():
    assert format_key("KEY_SPACE") == " "
    assert format_key("KEY_TAB") == "\t"
    assert format_key("KEY_ENTER") == "\n"


def test_numpad_keys():
    assert format_key("KEY_KP5") == "5"
    assert format_key("KEY_KPENTER") == "\n"
    assert format_key("KEY_KPPLUS") == "+"
    assert format_key("KEY_KPDOT") == "."


def test_special_keys_get_readable_tags():
    assert format_key("KEY_BACKSPACE") == "[BKSP]"
    assert format_key("KEY_ESC") == "[ESC]"
    assert format_key("KEY_UP") == "[UP]"


def test_unknown_keys_keep_their_evdev_name():
    assert format_key("KEY_F12") == "[F12]"
    assert format_key("BTN_LEFT") == "[BTN_LEFT]"
