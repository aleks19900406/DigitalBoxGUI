"""Box marks: names of inputs/outputs/sliders for one test device, stored as data/boxMarks/<name>.json.

JSON example (only the sections and indexes you need; unused ones can be left out):
    {
      "INPUT": {"0": "PR1", "1": "FAN", "8": "PUMP"},
      "OUTPUT": {"0": "LOCK", "1": "DOOR"},
      "DIGITAL_POT": {"0": "PT1000", "1": "MEAT"},
      "SET_FREQ": "SetFreq(Duty50%)",
      "AUTO1": {"name": "FLAPauto", "input": 19, "output": 15, "mode": "POSITIVE"}
    }
A section may also be a plain list: "OUTPUT": ["LOCK", "DOOR", "", "", "", "", "OUT6"].
"LABELS": {"<object name of a widget>": "text"} renames any other text/button of the GUI (EDIT LAYOUT, double click).
Old .txt box marks are still read when there is no .json with the same name.
"""

import json
import os
import re
import shutil
from .paths import BOX_MARKS_PATH

LIST_SECTIONS = ("INPUT", "OUTPUT", "DIGITAL_POT", "DAC_POT", "READ_ADC", "SET_VOLTAGE",
                 "READ_PWM1", "READ_PWM2", "SET_PWM1", "SET_PWM2")
TEXT_SECTIONS = ("SET_FREQ", "SET_DUTY")
AUTO_SECTIONS = ("AUTO1", "AUTO2", "AUTO3", "AUTO4")
LEGACY_ORDER = LIST_SECTIONS[:8] + ("SET_PWM1", "SET_PWM2") + TEXT_SECTIONS + AUTO_SECTIONS
README_FILES = ("readMe.txt", "readMe.md")
LABELS = "LABELS"
# GUI widgets whose text is a name from a box mark section: (object name, section, default name)
INDEXED_WIDGETS = (
    (re.compile(r"INPUT_(\d+)"), "INPUT", "IN{}"),
    (re.compile(r"OUT(\d+)"), "OUTPUT", "out{}"),
    (re.compile(r"labelDigitalPot(\d+)"), "DIGITAL_POT", "digitalPot{}"),
    (re.compile(r"labelADC(\d+)"), "READ_ADC", "ADC{}"),
    (re.compile(r"labelSetVoltage(\d+)"), "SET_VOLTAGE", "VOLTAGE{}"),
    (re.compile(r"labelPwm1_(\d+)"), "READ_PWM1", None),
    (re.compile(r"labelPwm2_(\d+)"), "READ_PWM2", None),
    (re.compile(r"labelSetPwm1_(\d+)"), "SET_PWM1", None),
    (re.compile(r"labelSetPwm2_(\d+)"), "SET_PWM2", None),
)
FIXED_WIDGETS = {"labelSetPwm3_0": "SET_FREQ", "labelSetPwm3_1": "SET_DUTY"}
AUTO_WIDGET = re.compile(r"AUTO([1-4])")


def list_box_marks():
    """Names of all box marks in data/boxMarks (json first, old txt only when there is no json of the same name)."""
    names = []
    for file_name in sorted(os.listdir(BOX_MARKS_PATH)):
        if file_name in README_FILES:
            continue
        stem, extension = os.path.splitext(file_name)
        if extension.lower() == ".json" and stem not in names:
            names.append(stem)
    for file_name in sorted(os.listdir(BOX_MARKS_PATH)):
        stem, extension = os.path.splitext(file_name)
        if file_name not in README_FILES and extension.lower() == ".txt" and stem not in names:
            names.append(stem)
    return names


def box_mark_path(name):
    """Path of the box mark file: the .json if it exists, otherwise the old .txt."""
    json_path = os.path.join(BOX_MARKS_PATH, f"{name}.json")
    return json_path if os.path.isfile(json_path) else os.path.join(BOX_MARKS_PATH, f"{name}.txt")


def load_box_mark(name):
    """Return {section: list of names | text | [name, input, output, mode, pulse_ms]} of the box mark."""
    path = box_mark_path(name)
    if path.endswith(".json"):
        raw = _read_json(path)
    else:
        with open(path, "r") as file:
            raw = _legacy_sections(file.read().splitlines())
    return _normalize(raw)


def box_mark_name(data, section, index, default):
    """Name at `index` of `section`, `default` when it is missing or empty."""
    values = data.get(section) if data else None
    if isinstance(values, list) and index < len(values) and values[index]:
        return values[index]
    return default


def widget_mark(object_name):
    """(section, index, default text) where the box mark keeps the text of this widget.
    Other widgets are kept in the LABELS section: ("LABELS", object name, None)."""
    for pattern, section, default in INDEXED_WIDGETS:
        match = pattern.fullmatch(object_name)
        if match:
            index = int(match.group(1))
            return section, index, default.format(index) if default else None
    if object_name in FIXED_WIDGETS:
        return FIXED_WIDGETS[object_name], 0, None
    match = AUTO_WIDGET.fullmatch(object_name)
    if match:
        return f"AUTO{match.group(1)}", 0, None
    return LABELS, object_name, None


def set_box_mark_value(box_mark, section, value, index=0):
    """Write one name into data/boxMarks/<box_mark>.json (an old .txt box mark is converted to .json first).
    `index` is the position in a list section, the widget object name for LABELS. An empty value removes the entry."""
    json_path = os.path.join(BOX_MARKS_PATH, f"{box_mark}.json")
    if not os.path.isfile(json_path):
        convert_txt_to_json(box_mark)
        old_folder = os.path.join(BOX_MARKS_PATH, "old_txt")
        os.makedirs(old_folder, exist_ok=True)
        shutil.move(os.path.join(BOX_MARKS_PATH, f"{box_mark}.txt"), os.path.join(old_folder, f"{box_mark}.txt"))
    raw = _read_json(json_path)
    if section in LIST_SECTIONS:
        names = raw.setdefault(section, {})
        if isinstance(names, list):
            names.extend([""] * (index + 1 - len(names)))
            names[index] = value
        elif value:
            names[str(index)] = value
        else:
            names.pop(str(index), None)
    elif section in AUTO_SECTIONS:
        auto = raw.setdefault(section, {})
        if isinstance(auto, list):
            auto[:1] = [value]
        else:
            auto["name"] = value
    elif section == LABELS:
        labels = raw.setdefault(LABELS, {})
        if value:
            labels[index] = value
        else:
            labels.pop(index, None)
    else:
        raw[section] = value
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(raw, file, indent=2, ensure_ascii=False)
        file.write("\n")


def _read_json(path):
    """Content of a json box mark (an empty file is an empty box mark)."""
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
    return json.loads(text) if text.strip() else {}


def valid_box_mark_name(name):
    """A box mark name is a usable file name that is not the readMe."""
    return (bool(name) and not re.search(r'[\\/:*?"<>|]', name) and not name.startswith(".")
            and f"{name}.txt" not in README_FILES and f"{name}.md" not in README_FILES)


def create_box_mark(name):
    """Create an empty data/boxMarks/<name>.json."""
    with open(os.path.join(BOX_MARKS_PATH, f"{name}.json"), "x", encoding="utf-8") as file:
        file.write("{}\n")


def _legacy_sections(lines):
    """Old format: a section name line followed by a line with comma separated names."""
    raw = {}
    for position, line in enumerate(lines):
        section = line.strip()
        if section in LEGACY_ORDER and position + 1 < len(lines):
            values = lines[position + 1]
            if section in TEXT_SECTIONS:
                raw[section] = values.strip()
            else:
                raw[section] = [value.strip() for value in values.split(",")]
    return raw


def _normalize(raw):
    data = {}
    for section in LIST_SECTIONS:
        values = raw.get(section)
        if isinstance(values, dict):
            size = max((int(key) for key in values), default=-1) + 1
            names = [""] * size
            for key, value in values.items():
                names[int(key)] = str(value).strip()
            data[section] = names
        elif isinstance(values, list):
            data[section] = [str(value).strip() for value in values]
    for section in TEXT_SECTIONS:
        if section in raw:
            data[section] = str(raw[section]).strip()
    if isinstance(raw.get(LABELS), dict):
        data[LABELS] = {str(name): str(text) for name, text in raw[LABELS].items()}
    for section in AUTO_SECTIONS:
        value = raw.get(section)
        if isinstance(value, dict):
            value = [value.get("name", ""), value.get("input", ""), value.get("output", ""),
                     value.get("mode", ""), value.get("pulse_ms", "")]
            while value and value[-1] == "":
                value.pop()
        if isinstance(value, list):
            data[section] = [str(item).strip() for item in value]
    return data


def convert_txt_to_json(name):
    """Write data/boxMarks/<name>.json from the old <name>.txt and return its path."""
    with open(os.path.join(BOX_MARKS_PATH, f"{name}.txt"), "r") as file:
        data = _normalize(_legacy_sections(file.read().splitlines()))
    raw = {}
    for section, values in data.items():
        if section in LIST_SECTIONS:
            raw[section] = {str(index): value for index, value in enumerate(values) if value}
        elif section in AUTO_SECTIONS:
            params = values + [""] * (5 - len(values))
            auto = {"name": params[0], "input": _number(params[1]), "output": _number(params[2]), "mode": params[3]}
            if params[4]:
                auto["pulse_ms"] = _number(params[4])
            raw[section] = auto
        else:
            raw[section] = values
    path = os.path.join(BOX_MARKS_PATH, f"{name}.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(raw, file, indent=2, ensure_ascii=False)
        file.write("\n")
    return path


def _number(text):
    return int(text) if text.isdigit() else text
