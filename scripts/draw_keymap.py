"""Converts keyboard.toml into a keymap-drawer keymap, for the layout image.

keymap-drawer parses ZMK and QMK keymaps but not RMK's, so this script writes
its keymap format directly. The legends follow the ones the ZMK config used.

    python scripts/draw_keymap.py > keymap-drawer/sweep36.json
    keymap -c keymap_drawer_config.yaml draw keymap-drawer/sweep36.json -o keymap-drawer/sweep36.svg

The output is JSON, which keymap-drawer reads as YAML.
"""

import json
import re
import sys
import tomllib

LAYOUT_JSON = "keymap-drawer/sweep36_layout.json"
TRANS = {"t": "▽", "type": "trans"}

# Legends for aliases, looked up by alias name so a swapped keycode keeps its meaning
ALIASES = {
    "sqm": "'", "dqm": '"', "bm": "`", "lca_tab": "CTRL+ ⌥+⭾", "redo": "↷",
    "scroll_up": "△ SCROLL", "scroll_down": "▽ SCROLL",
    "bt_next": "BT NXT", "bt_prev": "BT PRV", "bt_clear": "BT CLR", "out_toggle": "USB/BLE",
}
ALIASES.update({f"bt{i}": {"t": "BT", "h": str(i)} for i in range(4)})
PLAIN = {
    "Semicolon": ";", "Comma": ",", "Dot": ".", "Slash": "/", "Escape": "ESC", "Space": "␣", "Tab": "⭾",
    "Enter": "⏎", "Backspace": "⌫", "Delete": "⌦", "Home": "HOME", "End": "END", "PageUp": "PAG▲",
    "PageDown": "PAG▼", "Up": "▲", "Down": "▼", "Left": "◀", "Right": "▶", "CapsLock": "🄰 CAPS",
    "NumLock": "NUM", "Insert": "⎀INS", "Application": "☰", "Undo": "↶", "Cut": "✂", "Copy": "COPY",
    "Paste": "PASTE", "ScrollLock": "SCROLL LOCK", "PrintScreen": "⎙",
    # A bare dead key on an international layout waits for the next key
    "Grave": "` INTL.", "Quote": "' INTL.", "Equal": "=", "Minus": "-", "Backslash": "\\",
    "LeftBracket": "[", "RightBracket": "]",
    "LGui": "⌘", "RGui": "⌘", "LAlt": "⌥", "RAlt": "AltGr", "LCtrl": "CTRL", "RCtrl": "CTRL",
    "LShift": "⇧", "RShift": "⇧",
    "MouseBtn1": "LEFT CLICK", "MouseBtn2": "RIGHT CLICK", "MouseBtn3": "MIDDLE CLICK", "MouseBtn4": "⎗",
    "MouseBtn5": "⎘", "MouseUp": "▲ MOUSE", "MouseDown": "▼ MOUSE", "MouseLeft": "◀ MOUSE",
    "MouseRight": "▶ MOUSE", "MouseWheelLeft": "◁ SCROLL", "MouseWheelRight": "▷ SCROLL",
    "MediaRewind": "REWIND", "MediaFastForward": "FAST FORW", "MediaPlayPause": "⏯",
    "MediaPrevTrack": "⏮", "MediaNextTrack": "⏭", "AudioVolUp": "🕪", "AudioVolDown": "🕩", "AudioMute": "🕨",
    "Bootloader": "BOOT", "ClearEeprom": "CLR EEPROM", "No": "",
}
PLAIN.update({f"Kc{i}": str(i) for i in range(10)})
PLAIN.update({f"F{i}": f"F{i}" for i in range(1, 13)})
PLAIN.update({c: c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"})
SHIFTED = {
    "Quote": '" INTL.', "Grave": "~ INTL.", "Kc6": "^ INTL.", "LeftBracket": "{", "RightBracket": "}",
    "Kc1": "!", "Kc2": "@", "Kc3": "#", "Kc4": "$", "Kc5": "%", "Kc7": "&", "Kc8": "*", "Kc9": "(", "Kc0": ")",
    "Backslash": "|", "Minus": "_", "Comma": "<", "Dot": ">", "Equal": "+",
}


def split_actions(keys):
    """Splits a layer's key string on whitespace outside parentheses."""
    return re.findall(r"(?:[^\s(]|\([^)]*\))+", keys)


def legend(action):
    if action == "_":
        return TRANS
    if action.startswith("@"):
        return ALIASES[action[1:]]
    if m := re.fullmatch(r"SHIFTED\((\w+)\)", action):
        return SHIFTED[m[1]]
    if m := re.fullmatch(r"LT\((\w+), (\w+), \w+\)", action):
        return {"t": PLAIN[m[2]], "h": m[1]}
    if m := re.fullmatch(r"MT\((\w+), (\w+), \w+\)", action):
        return {"t": PLAIN[m[1]], "h": PLAIN[m[2]]}
    return PLAIN[action]


def main():
    with open("keyboard.toml", "rb") as f:
        config = tomllib.load(f)
    layers = config["keymap"]["layer"]
    names = [layer["name"] for layer in layers]
    actions = [split_actions(layer["keys"]) for layer in layers]

    drawn = {name: [legend(a) for a in keys] for name, keys in zip(names, actions)}
    # Mark the key held to reach each layer, where that layer leaves it transparent
    for pos, action in enumerate(actions[0]):
        if m := re.match(r"LT\((\w+),", action):
            if drawn[m[1]][pos] == TRANS:
                drawn[m[1]][pos] = {"type": "held"}

    combos = []
    for combo in config["behavior"]["combo"]["combos"]:
        layer = combo["layer"]
        positions = [actions[layer].index(a) for a in combo["actions"]]
        # The same combo on several layers draws once, listing all of them
        for drawn_combo in combos:
            if drawn_combo["p"] == positions and drawn_combo["k"] == combo["output"]:
                drawn_combo["l"].append(names[layer])
                break
        else:
            combos.append({"p": positions, "k": combo["output"], "l": [names[layer]]})
    for drawn_combo in combos:
        drawn_combo["k"] = {"CapsWordToggle": "CAPS WORD"}[drawn_combo["k"]]

    keymap = {"layout": {"qmk_info_json": LAYOUT_JSON}, "layers": drawn, "combos": combos}
    sys.stdout.reconfigure(encoding="utf-8")
    json.dump(keymap, sys.stdout, ensure_ascii=False, indent=1)
    print()


main()
