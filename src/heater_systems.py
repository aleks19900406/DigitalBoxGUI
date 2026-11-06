"""Detect the running oven system from the digital inputs (heatersON column of digital_input.xlsx)."""

import re
import traceback
import openpyxl
from .paths import PROJECT_ROOT

HEATER_SPEC_PATH = PROJECT_ROOT / "specification" / "digital_input.xlsx"
BOX_MARK_SHEETS = {
    "BIO24_GHA800": "G800",
    "BIO24_Elements_CraftF": "Elements",
    "BIO24_CraftG": "CraftG",
}


def load_heater_systems(box_mark):
    """Return [(system name, set of heater inputs)] for the sheet that belongs to the box mark."""
    try:
        workbook = openpyxl.load_workbook(HEATER_SPEC_PATH, read_only=True, data_only=True)
    except Exception:
        with open('check_error.txt', 'a') as f:
            f.write(traceback.format_exc())
        return []
    try:
        sheet_name = BOX_MARK_SHEETS.get(box_mark)
        if sheet_name is None:
            sheet_name = next((name for name in workbook.sheetnames if name.lower() in str(box_mark).lower()), None)
        if sheet_name not in workbook.sheetnames:
            return []
        rows = workbook[sheet_name].iter_rows(values_only=True)
        header = [str(cell).strip() if cell is not None else "" for cell in next(rows, ())]
        if "system" not in header or "heatersON" not in header or "heatersOFF" not in header:
            return []
        system_column = header.index("system")
        on_column, off_column = header.index("heatersON"), header.index("heatersOFF")
        systems = []
        for row in rows:
            if len(row) <= max(system_column, on_column, off_column):
                continue
            name = row[system_column]
            heaters_on, heaters_off = _heater_inputs(row[on_column]), _heater_inputs(row[off_column])
            if name is None or not heaters_on:
                continue
            systems.append((str(name).strip(), heaters_on, heaters_off))
        return systems
    finally:
        workbook.close()


def _heater_inputs(cell):
    """'06,07,10.11' -> {6, 7, 10, 11}"""
    if cell is None:
        return frozenset()
    if isinstance(cell, float):  # Excel turns '10.10' into 10.1
        cell = f"{cell:.2f}"
    return frozenset(int(number) for number in re.findall(r"\d+", str(cell)))


def detect_systems(systems, active_inputs):
    """All systems (in table order) whose heatersON are all on and heatersOFF are all off."""
    return [name for name, heaters_on, heaters_off in systems
            if heaters_on <= active_inputs and not heaters_off & active_inputs]


def display_name(name):
    """SubBottomTop1 -> Bottom Top"""
    name = re.sub(r"^sub", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\d+$", "", name)
    name = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", name)
    return name.strip()
