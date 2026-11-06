"""Compact layout for small displays (Raspberry Pi): only the connection, the ON/OFF button, the digital
potentiometers and the digital outputs, as large as the screen allows."""
import os
import re
import sys

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QPushButton

from .styles import ACCENT, arrow_image

# BOX_GUI_COMPACT=1 / 0 forces the compact / the full layout, otherwise the compact one is used on Linux
# when the screen is smaller than the full form
ENVIRONMENT_VARIABLE = "BOX_GUI_COMPACT"
POT_SLIDER_HEIGHT = 340
POT_SLIDER_WIDTH = 88
# a thicker groove and a large handle that is easy to grab with a finger (the colors come from the theme)
POT_SLIDER_STYLE = (
    "QSlider { background: transparent; }"
    "QSlider::groove:vertical { background: transparent; width: 20px; border-radius: 10px; }"
    f"QSlider::add-page:vertical {{ background: {ACCENT}; width: 20px; border-radius: 10px; }}"
    "QSlider::sub-page:vertical { background: palette(mid); width: 20px; border-radius: 10px; }"
    f"QSlider::handle:vertical {{ background: palette(base); border: 4px solid {ACCENT};"
    " height: 56px; margin: 0 -30px; border-radius: 30px; }")
POT_FOLLOWERS = ("PotMin", "lcdNumber_digital_pot", "labelDigitalPot")
POT_WIDGET = re.compile(r"^(?:digital_pot|PotMin|PotMax|lcdNumber_digital_pot|labelDigitalPot)\d+$")
OUTPUT_COLUMNS = 4
OUTPUT_ORIGIN = (650, 190)
OUTPUT_STEP = (120, 64)
OUTPUT_SIZE = (110, 56)
# the output and AUTO buttons have this much larger text and icon
BUTTON_SCALE = 1.5
# the connection part (combo boxes, refresh and ON/OFF button) is this many times larger
CONNECTION_SCALE = 2
# the pots and the outputs start below the (higher) connection part
POT_SHIFT = 60
CONNECTION_SIZES = {"BoxConnect": (402, 62), "connectBar": (402, 62), "BoxMarks": (402, 62),
                    "RefreshingConnection": (140, 140), "on_off": (140, 140)}
FONT_PIXELS = re.compile(r"(font:[^;]*?)(\d+)px")
# the connection combo boxes: width of the drop-down button, size of its arrow and height of a list item
COMBO_BUTTON_WIDTH = 72
COMBO_ARROW_SIZE = 28
COMBO_ITEM_HEIGHT = 64
# dialogs on the small screen
DIALOG_FONT_PIXELS = 26
DIALOG_BUTTON_HEIGHT = 64
DIALOG_FIELD_HEIGHT = 56
DIALOG_BUTTON_WIDTH = 170
DIALOG_WIDTH = 720
# the texts below the sliders (pot name, min and max value) are this many times larger
POT_TEXT_SCALE = 1.5
POT_TEXT_SIZES = {"labelDigitalPot": (96, 40), "PotMin": (64, 20), "PotMax": (64, 20)}
# the AUTO buttons (2 x 2) are below the outputs, each as wide as two outputs
AUTO_BUTTON_SIZE = (230, 52)
# TEMP RAMP, REG TEMP, TOGGLE OUT and SERVICES are as large as the AUTO buttons, 2 x 2 right of the ON/OFF button
# (above the outputs, right of EDIT LAYOUT)
TOOL_BUTTON_SIZE = AUTO_BUTTON_SIZE
TOOL_ORIGIN = (1030, 10)
TOOL_STEP = (240, 62)
TOOL_BUTTONS = ("rampButton", "regButton", "toggleButton", "servicesButton")
# EDIT LAYOUT and RESET LAYOUT (created later by the layout editor) are as large, left of them
EDITOR_BUTTONS = ("editLayoutButton", "resetLayoutButton")
# their style sheets have a 10 px font, the AUTO buttons have 18 px
TOOL_FONT_SCALE = 1.8
AUTO_ORIGIN = (650, 490)
AUTO_STEP = (240, 62)
# the digital inputs are below the sliders and outputs; only the inputs with a name in the box marks are shown,
# one after another
INPUT_COLUMNS = 11
INPUT_ORIGIN = (20, 635)
INPUT_STEP = (102, 50)
INPUT_SIZE = (98, 44)
INPUT_COUNT = 32


def input_slot(position):
    return (INPUT_ORIGIN[0] + INPUT_STEP[0] * (position % INPUT_COLUMNS),
            INPUT_ORIGIN[1] + INPUT_STEP[1] * (position // INPUT_COLUMNS))


POSITIONS = {
    "BoxConnect": (20, 5),
    "connectBar": (20, 5),
    "BoxMarks": (20, 77),
    "RefreshingConnection": (440, 5),
    "on_off": (600, 5),
    "editLayoutButton": (780, TOOL_ORIGIN[1]),
    "resetLayoutButton": (780, TOOL_ORIGIN[1] + TOOL_STEP[1]),
    "rampButton": (TOOL_ORIGIN[0], TOOL_ORIGIN[1]),
    "regButton": (TOOL_ORIGIN[0] + TOOL_STEP[0], TOOL_ORIGIN[1]),
    "toggleButton": (TOOL_ORIGIN[0], TOOL_ORIGIN[1] + TOOL_STEP[1]),
    "servicesButton": (TOOL_ORIGIN[0] + TOOL_STEP[0], TOOL_ORIGIN[1] + TOOL_STEP[1]),
    "label_marks_3": (650, 150),
    "label_marks_12": (650, 450),
    **{f"AUTO{number}": (AUTO_ORIGIN[0] + AUTO_STEP[0] * ((number - 1) % 2),
                        AUTO_ORIGIN[1] + AUTO_STEP[1] * ((number - 1) // 2))
       for number in range(1, 5)},
    **{f"OUT{index}": (OUTPUT_ORIGIN[0] + OUTPUT_STEP[0] * (index % OUTPUT_COLUMNS),
                       OUTPUT_ORIGIN[1] + OUTPUT_STEP[1] * (index // OUTPUT_COLUMNS))
       for index in range(16)},
    **{f"INPUT_{index}": input_slot(index) for index in range(INPUT_COUNT)},
}


def compact_layout_wanted():
    from .layout_mode import FULL_WINDOW_HEIGHT, FULL_WINDOW_WIDTH  # layout_mode imports this module
    forced = os.environ.get(ENVIRONMENT_VARIABLE)
    if forced is not None:
        return forced.strip().lower() in ("1", "true", "yes", "on")
    if not sys.platform.startswith("linux"):
        return False
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return False
    area = screen.availableGeometry()
    return area.width() < FULL_WINDOW_WIDTH or area.height() < FULL_WINDOW_HEIGHT


def shrink_pots(window):
    """The sliders are shorter, so the whole form is lower (and therefore larger on a small screen)."""
    for index in range(6):
        slider = getattr(window, f"digital_pot{index}")
        delta = slider.height() - POT_SLIDER_HEIGHT
        if delta <= 0:
            continue
        slider.setGeometry(slider.x() - (POT_SLIDER_WIDTH - slider.width()) // 2, slider.y(),
                           POT_SLIDER_WIDTH, POT_SLIDER_HEIGHT)
        slider.setStyleSheet(POT_SLIDER_STYLE)
        slider.setProperty("compact_slider", True)
        for prefix in POT_FOLLOWERS:
            widget = getattr(window, f"{prefix}{index}")
            widget.move(widget.x(), widget.y() - delta)
        for prefix in ("digital_pot", "PotMax") + POT_FOLLOWERS:
            widget = getattr(window, f"{prefix}{index}")
            widget.move(widget.x(), widget.y() + POT_SHIFT)


def _scale_font_pixels(style, factor=CONNECTION_SCALE):
    return FONT_PIXELS.sub(lambda match: f"{match.group(1)}{round(int(match.group(2)) * factor)}px", style)


def _combo_style(style):
    """Larger text, a wide drop-down button with a big arrow and tall list items (easy to hit with a finger)."""
    if "{" not in style:
        style = f"* {{ {style} }}"
    arrow = arrow_image("down", ACCENT, COMBO_ARROW_SIZE)
    return (_scale_font_pixels(style)
            + f" QComboBox::drop-down {{ width: {COMBO_BUTTON_WIDTH}px; }}"
            + f" QComboBox::down-arrow {{ image: url({arrow}); width: {COMBO_ARROW_SIZE}px; height: {COMBO_ARROW_SIZE}px; }}"
            + f" QComboBox QAbstractItemView::item {{ min-height: {COMBO_ITEM_HEIGHT}px; }}")


def enlarge_connection(window):
    """The connection part is 2x larger (size, font, icon); later style changes keep the larger font."""
    for name, size in CONNECTION_SIZES.items():
        widget = getattr(window, name)
        if widget.width() >= size[0] and widget.height() >= size[1]:
            continue
        widget.resize(*size)
        font = widget.font()
        if font.pointSizeF() > 0:
            font.setPointSizeF(font.pointSizeF() * CONNECTION_SCALE)
            widget.setFont(font)
        if name in ("BoxConnect", "BoxMarks"):
            set_style = widget.setStyleSheet
            set_style(_combo_style(widget.styleSheet()))
            widget.setStyleSheet = lambda style, set_style=set_style: set_style(_combo_style(style))
        else:
            widget.setStyleSheet(_scale_font_pixels(widget.styleSheet()))
        if name in ("RefreshingConnection", "on_off"):
            widget.setIconSize(widget.iconSize() * CONNECTION_SCALE)


def enlarge_dialog(dialog):
    """Large text, a tall input and big buttons so a dialog (e.g. choosing the box) is easy to use with a finger."""
    arrow = arrow_image("down", ACCENT, COMBO_ARROW_SIZE)
    up_arrow = arrow_image("up", ACCENT, COMBO_ARROW_SIZE)
    spins = "QSpinBox, QDoubleSpinBox, QTimeEdit"
    dialog.setStyleSheet(
        f"* {{ font-size: {DIALOG_FONT_PIXELS}px; }}"
        f" QPushButton {{ min-height: {DIALOG_BUTTON_HEIGHT}px; min-width: {DIALOG_BUTTON_WIDTH}px; }}"
        f" QComboBox {{ min-height: {DIALOG_FIELD_HEIGHT}px; }}"
        f" QComboBox::drop-down {{ width: {COMBO_BUTTON_WIDTH}px; }}"
        f" QComboBox::down-arrow {{ image: url({arrow}); width: {COMBO_ARROW_SIZE}px; height: {COMBO_ARROW_SIZE}px; }}"
        f" QComboBox QAbstractItemView::item {{ min-height: {COMBO_ITEM_HEIGHT}px; }}"
        # number fields: a big minus button on the left and a big plus button on the right, the value in the middle
        f" {spins} {{ min-height: {DIALOG_FIELD_HEIGHT}px; padding-left: {COMBO_BUTTON_WIDTH + 4}px;"
        f" padding-right: {COMBO_BUTTON_WIDTH + 4}px; border: 1px solid palette(mid); border-radius: 6px;"
        " background-color: palette(base); color: palette(text); }"
        f" QSpinBox::up-button, QDoubleSpinBox::up-button, QTimeEdit::up-button {{ subcontrol-origin: border;"
        f" subcontrol-position: right; width: {COMBO_BUTTON_WIDTH}px; height: {DIALOG_FIELD_HEIGHT - 2}px; border: none;"
        " border-left: 1px solid palette(mid); background: palette(alternate-base); }"
        f" QSpinBox::down-button, QDoubleSpinBox::down-button, QTimeEdit::down-button {{ subcontrol-origin: border;"
        f" subcontrol-position: left; width: {COMBO_BUTTON_WIDTH}px; height: {DIALOG_FIELD_HEIGHT - 2}px; border: none;"
        " border-right: 1px solid palette(mid); background: palette(alternate-base); }"
        f" QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QTimeEdit::up-arrow {{ image: url({up_arrow});"
        f" width: {COMBO_ARROW_SIZE}px; height: {COMBO_ARROW_SIZE}px; }}"
        f" QSpinBox::down-arrow, QDoubleSpinBox::down-arrow, QTimeEdit::down-arrow {{ image: url({arrow});"
        f" width: {COMBO_ARROW_SIZE}px; height: {COMBO_ARROW_SIZE}px; }}"
        f" QProgressBar {{ min-height: {COMBO_ITEM_HEIGHT // 2}px; }}")
    # the START / STOP buttons have their own small font; keep it large when their style changes
    factor = DIALOG_FONT_PIXELS / 10
    for button in dialog.findChildren(QPushButton):
        button.setStyleSheet(_scale_font_pixels(button.styleSheet(), factor))
        set_style = button.setStyleSheet
        button.setStyleSheet = lambda style, set_style=set_style: set_style(_scale_font_pixels(style, factor))
    screen = QGuiApplication.primaryScreen()
    available = screen.availableGeometry().width() - 20 if screen is not None else DIALOG_WIDTH
    dialog.setMinimumWidth(min(DIALOG_WIDTH, available))
    dialog.setMaximumWidth(available)


def enlarge_pot_texts(window):
    """The pot names, and the min / max values are larger; later style changes keep the larger text."""
    for index in range(6):
        for prefix, size in POT_TEXT_SIZES.items():
            widget = getattr(window, f"{prefix}{index}")
            center = widget.x() + widget.width() // 2
            widget.setGeometry(center - size[0] // 2, widget.y(), *size)
            font = widget.font()
            if font.pointSizeF() > 0:
                font.setPointSizeF(font.pointSizeF() * POT_TEXT_SCALE)
                widget.setFont(font)
            widget.setStyleSheet(_scale_font_pixels(widget.styleSheet(), POT_TEXT_SCALE))
            set_style = widget.setStyleSheet
            widget.setStyleSheet = lambda style, set_style=set_style: set_style(_scale_font_pixels(style, POT_TEXT_SCALE))


def enlarge_buttons(window, only=None):
    """The digital output, input, AUTO and tool buttons are larger (only: just these names); later style changes
    keep the larger text."""
    sizes = {f"OUT{index}": OUTPUT_SIZE for index in range(16)}
    sizes.update({f"INPUT_{index}": INPUT_SIZE for index in range(INPUT_COUNT)})
    sizes.update({f"AUTO{number}": AUTO_BUTTON_SIZE for number in range(1, 5)})
    sizes.update({name: TOOL_BUTTON_SIZE for name in TOOL_BUTTONS})
    if only is not None:  # the editor buttons do not exist yet when all the buttons are enlarged at the start
        sizes.update({name: TOOL_BUTTON_SIZE for name in EDITOR_BUTTONS})
    for name, size in sizes.items():
        if only is not None and name not in only:
            continue
        button = getattr(window, name)
        scale = TOOL_FONT_SCALE if name in TOOL_BUTTONS + EDITOR_BUTTONS else BUTTON_SCALE
        button.resize(*size)
        button.setIconSize(button.iconSize() * BUTTON_SCALE)
        font = button.font()
        if font.pointSizeF() > 0:
            font.setPointSizeF(font.pointSizeF() * BUTTON_SCALE)
            button.setFont(font)
        button.setStyleSheet(_scale_font_pixels(button.styleSheet(), scale))
        set_style = button.setStyleSheet
        button.setStyleSheet = lambda style, set_style=set_style, scale=scale: set_style(_scale_font_pixels(style, scale))


def compact_inputs_arranged(window):
    """True on a small screen while the inputs are still where the compact layout put them (not moved by the user)."""
    positions = getattr(window, "custom_positions", None) or {}
    return compact_layout_wanted() and tuple(positions.get("INPUT_0", ())) == input_slot(0)


def pack_inputs(window, shown):
    """The inputs in `shown` (indexes) are placed one after another, from the first slot."""
    for slot, index in enumerate(shown):
        getattr(window, f"INPUT_{index}").move(*input_slot(slot))


def compact_layout(window):
    """(positions, hidden controls): everything which is not in POSITIONS is deleted."""
    hidden = {widget.objectName() for widget in window._selectable_widgets()
              if widget.objectName() not in POSITIONS and not POT_WIDGET.match(widget.objectName())}
    return dict(POSITIONS), hidden
