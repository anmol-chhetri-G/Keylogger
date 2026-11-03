"""Pure key-formatting helpers for the evdev keylogger.

These functions translate evdev key names (e.g. ``KEY_A``) into the text a
keypress contributes to the log. They are hardware- and OS-independent, so
they can be unit-tested anywhere — no ``/dev/input`` access required.

The tables describe the US QWERTY layout.
"""

from __future__ import annotations

_LETTERS: dict[str, str] = {
    f"KEY_{letter}": letter.lower() for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
}

UNSHIFTED: dict[str, str] = {
    **{f"KEY_{digit}": digit for digit in "1234567890"},
    "KEY_GRAVE": "`",
    "KEY_MINUS": "-",
    "KEY_EQUAL": "=",
    "KEY_LEFTBRACE": "[",
    "KEY_RIGHTBRACE": "]",
    "KEY_BACKSLASH": "\\",
    "KEY_SEMICOLON": ";",
    "KEY_APOSTROPHE": "'",
    "KEY_COMMA": ",",
    "KEY_DOT": ".",
    "KEY_SLASH": "/",
    "KEY_SPACE": " ",
    "KEY_TAB": "\t",
    "KEY_ENTER": "\n",
    "KEY_KPENTER": "\n",
    **{f"KEY_KP{digit}": digit for digit in "0123456789"},
    "KEY_KPDOT": ".",
    "KEY_KPSLASH": "/",
    "KEY_KPASTERISK": "*",
    "KEY_KPMINUS": "-",
    "KEY_KPPLUS": "+",
}

SHIFTED: dict[str, str] = {
    "KEY_1": "!",
    "KEY_2": "@",
    "KEY_3": "#",
    "KEY_4": "$",
    "KEY_5": "%",
    "KEY_6": "^",
    "KEY_7": "&",
    "KEY_8": "*",
    "KEY_9": "(",
    "KEY_0": ")",
    "KEY_GRAVE": "~",
    "KEY_MINUS": "_",
    "KEY_EQUAL": "+",
    "KEY_LEFTBRACE": "{",
    "KEY_RIGHTBRACE": "}",
    "KEY_BACKSLASH": "|",
    "KEY_SEMICOLON": ":",
    "KEY_APOSTROPHE": '"',
    "KEY_COMMA": "<",
    "KEY_DOT": ">",
    "KEY_SLASH": "?",
}

# Friendlier tags than the raw evdev names for the most common special keys.
_SHORT_TAGS: dict[str, str] = {
    "KEY_ESC": "ESC",
    "KEY_BACKSPACE": "BKSP",
    "KEY_DELETE": "DEL",
    "KEY_INSERT": "INS",
    "KEY_HOME": "HOME",
    "KEY_END": "END",
    "KEY_PAGEUP": "PGUP",
    "KEY_PAGEDOWN": "PGDN",
    "KEY_UP": "UP",
    "KEY_DOWN": "DOWN",
    "KEY_LEFT": "LEFT",
    "KEY_RIGHT": "RIGHT",
}

# Keys that only modify other keys — tracked for state, but never logged.
MODIFIER_KEYS: frozenset[str] = frozenset({
    "KEY_LEFTCTRL",
    "KEY_RIGHTCTRL",
    "KEY_LEFTALT",
    "KEY_RIGHTALT",
    "KEY_LEFTSHIFT",
    "KEY_RIGHTSHIFT",
    "KEY_LEFTMETA",
    "KEY_RIGHTMETA",
    "KEY_CAPSLOCK",
    "KEY_NUMLOCK",
    "KEY_SCROLLLOCK",
    "KEY_FN",
})


def format_key(name: str, *, shift: bool = False, caps: bool = False) -> str:
    """Return the text a single keypress contributes to the log.

    Letters combine the shift and caps-lock state: either flag alone
    uppercases the letter, both together cancel back out (standard US
    keyboard behaviour).
    """
    if name in _LETTERS:
        letter = _LETTERS[name]
        return letter.upper() if shift ^ caps else letter
    if shift and name in SHIFTED:
        return SHIFTED[name]
    if name in UNSHIFTED:
        return UNSHIFTED[name]
    tag = _SHORT_TAGS.get(name, name)
    return f"[{tag.removeprefix('KEY_')}]"
