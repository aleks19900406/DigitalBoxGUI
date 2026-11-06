from PyQt6.QtCore import QPointF, QSettings, Qt
from PyQt6.QtGui import QColor, QPainter, QPalette, QPixmap, QPolygonF
from PyQt6.QtWidgets import QApplication
import tempfile
from pathlib import Path

ACCENT = "#2563eb"
ACCENT_DARK = "#1d4ed8"
ON_COLOR = "#22c55e"
ON_BORDER = "#16a34a"

THEMES = {
    "light": {
        "window": "#f3f5f8", "surface": "#ffffff", "hover": "#eef3fb", "pressed": "#dbe6f8",
        "text": "#1f2937", "title": "#1f2937", "muted": "#9aa3af",
        "disabled": "#eceff3", "disabled_border": "#dde2e8",
        "border": "#c9d1dc", "off": "#e5e7eb", "off_border": "#cbd2db", "off_text": "#374151",
        "track": "#dfe4ea", "handle": "#ffffff", "tooltip": "#111827", "tooltip_text": "#ffffff",
        "lcd": "#0f172a", "line_light": None, "line_dark": None,
    },
    "dark": {
        "window": "#0d0f12", "surface": "#1b1e24", "hover": "#262b34", "pressed": "#1e3a8a",
        "text": "#e5e7eb", "title": "#60a5fa", "muted": "#6b7280",
        "disabled": "#15171c", "disabled_border": "#272b33",
        "border": "#363c48", "off": "#23272f", "off_border": "#363c48", "off_text": "#cbd5e1",
        "track": "#363c48", "handle": "#e5e7eb", "tooltip": "#262b34", "tooltip_text": "#e5e7eb",
        "lcd": "#050608", "line_light": "#0d0f12", "line_dark": "#363c48",
    },
}


def arrow_image(direction, color, size=10):
    """Small triangle png for the spin box buttons (style sheets can only use image files)."""
    folder = Path(tempfile.gettempdir()) / "digital_box_arrows"
    folder.mkdir(exist_ok=True)
    path = folder / f"{direction}_{color.lstrip('#')}_{size}.png"
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / 10, size / 10)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    if direction == "up":
        points = [QPointF(1, 7), QPointF(9, 7), QPointF(5, 2)]
    else:
        points = [QPointF(1, 3), QPointF(9, 3), QPointF(5, 8)]
    painter.drawPolygon(QPolygonF(points))
    painter.end()
    pixmap.save(str(path))
    return path.as_posix()


def build_app_theme(c):
    up_arrow = arrow_image("up", c['text'])
    down_arrow = arrow_image("down", c['text'])
    return f"""
QMainWindow, QDialog, QWidget#centralwidget {{ background-color: {c['window']}; }}
QLabel {{ background: transparent; color: {c['text']}; }}
QLabel[sectionTitle="true"] {{ background-color: {c['window']}; color: {c['title']}; }}
QToolTip {{ background-color: {c['tooltip']}; color: {c['tooltip_text']}; border: 1px solid {c['border']}; padding: 4px 8px; border-radius: 4px; }}

QPushButton {{
    background-color: {c['surface']}; color: {c['text']};
    border: 1px solid {c['border']}; border-radius: 6px; padding: 2px 6px;
}}
QPushButton:hover {{ background-color: {c['hover']}; border-color: {ACCENT}; }}
QPushButton:pressed {{ background-color: {c['pressed']}; }}
QPushButton:disabled {{ color: {c['muted']}; background-color: {c['disabled']}; border-color: {c['disabled_border']}; }}
QPushButton#on_off, QPushButton#startStopSaving {{ background: transparent; border: none; }}

QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{
    background-color: {c['surface']}; color: {c['text']};
    border: 1px solid {c['border']}; border-radius: 6px; padding: 1px 6px;
    selection-background-color: {ACCENT};
}}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover,
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding; subcontrol-position: center right; width: 26px;
    border: none; border-left: 1px solid {c['border']}; border-top-right-radius: 6px; border-bottom-right-radius: 6px;
    background: {c['off']};
}}
QComboBox::drop-down:hover {{ background: {c['hover']}; }}
QComboBox::down-arrow {{ image: url({down_arrow}); width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{
    background: {c['surface']}; color: {c['text']}; border: 1px solid {c['border']}; outline: none;
    selection-background-color: {ACCENT}; selection-color: white;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border; subcontrol-position: top right; width: 22px; border: none;
    border-left: 1px solid {c['border']}; border-top-right-radius: 6px; background: {c['off']};
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border; subcontrol-position: bottom right; width: 22px; border: none;
    border-left: 1px solid {c['border']}; border-bottom-right-radius: 6px; background: {c['off']};
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{ background: {c['hover']}; }}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{ background: {c['pressed']}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url({up_arrow}); width: 10px; height: 10px; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url({down_arrow}); width: 10px; height: 10px; }}

QSlider {{ background: transparent; }}
QSlider::groove:vertical {{ background: transparent; width: 6px; border-radius: 3px; }}
QSlider::add-page:vertical {{ background: {ACCENT}; width: 6px; border-radius: 3px; }}
QSlider::sub-page:vertical {{ background: {c['track']}; width: 6px; border-radius: 3px; }}
QSlider::handle:vertical {{
    background: {c['handle']}; border: 2px solid {ACCENT};
    height: 16px; margin: 0 -8px; border-radius: 10px;
}}
QSlider::groove:horizontal {{ background: transparent; height: 6px; border-radius: 3px; }}
QSlider::add-page:horizontal {{ background: {c['track']}; height: 6px; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {ACCENT}; height: 6px; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: {c['handle']}; border: 2px solid {ACCENT};
    width: 16px; margin: -8px 0; border-radius: 10px;
}}
QSlider::handle:hover {{ background: {c['hover']}; border-color: {ACCENT_DARK}; }}
QSlider::handle:disabled {{ border-color: {c['muted']}; }}
QSlider::add-page:vertical:disabled, QSlider::sub-page:horizontal:disabled {{ background: {c['muted']}; }}

QScrollBar:horizontal {{ background: {c['track']}; height: 12px; border-radius: 6px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {ACCENT}; min-width: 28px; border-radius: 6px; }}
QScrollBar:vertical {{ background: {c['track']}; width: 12px; border-radius: 6px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {ACCENT}; min-height: 28px; border-radius: 6px; }}
QScrollBar::handle:hover {{ background: {ACCENT_DARK}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: none; background: none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

QLCDNumber {{ background-color: {c['lcd']}; color: #38bdf8; border: none; border-radius: 6px; }}

QProgressBar {{
    background-color: {c['track']}; border: none; border-radius: 6px;
    text-align: center; color: {c['text']};
}}
QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 6px; }}
"""


def build_palette(app, c):
    """Palette roles are used by the per-widget styles below (palette(...)), so they follow the theme."""
    palette = app.style().standardPalette()
    roles = {
        QPalette.ColorRole.Window: c["window"], QPalette.ColorRole.WindowText: c["text"],
        QPalette.ColorRole.Base: c["surface"], QPalette.ColorRole.AlternateBase: c["off"],
        QPalette.ColorRole.Text: c["text"], QPalette.ColorRole.Button: c["surface"], QPalette.ColorRole.ButtonText: c["off_text"],
        QPalette.ColorRole.Mid: c["off_border"], QPalette.ColorRole.Highlight: ACCENT, QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.ToolTipBase: c["tooltip"], QPalette.ColorRole.ToolTipText: c["tooltip_text"],
        QPalette.ColorRole.Light: c["line_light"], QPalette.ColorRole.Dark: c["line_dark"],
    }
    for role, color in roles.items():
        if color:
            palette.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(c["muted"]))
    return palette


def saved_theme():
    name = QSettings("DigitalBox", "BOX_GUI").value("theme", "light")
    return name if name in THEMES else "light"


def apply_theme(name):
    app = QApplication.instance()
    colors = THEMES.get(name, THEMES["light"])
    app.setPalette(build_palette(app, colors))
    app.setStyleSheet(build_app_theme(colors))
    QSettings("DigitalBox", "BOX_GUI").setValue("theme", name)


ButtonStyleOnOff = ("background-color: palette(base);"
                    "border: 1px solid palette(mid); border-radius: 6px;"
                    "font: 10px;")

ButtonStyleOff2  = ("background-color: palette(alternate-base); color: palette(button-text);"
                    "border: 1px solid palette(mid); border-radius: 6px;"
                    "font: 10px;")

ButtonStyleOn2  = (f"background-color: {ON_COLOR}; color: white;"
                   f"border: 1px solid {ON_BORDER}; border-radius: 6px;"
                   "font: bold 10px;")

ButtonStyleOff  = ("background-color: palette(alternate-base); color: palette(button-text);"
                   "border: 1px solid palette(mid); border-radius: 6px;"
                   "font: 10px;")

ButtonStyleOn  = (f"background-color: {ON_COLOR}; color: white;"
                  f"border: 1px solid {ON_BORDER}; border-radius: 6px;"
                  "font: bold 12px;")

ButtonStyleWhite = ("background-color: palette(base); color: palette(text);"
                    "border: 1px solid palette(mid); border-radius: 6px;"
                    "font: 12px;")

MainScreenStyle = "QMainWindow, QDialog, QWidget#centralwidget { background-color: palette(window); }"

PotSlicerLabelStyle = ("background-color: palette(base); color: palette(text);"
                       "border: 1px solid palette(mid); border-radius: 6px;"
                       "font: 12px;")

InputStyleOn  = (f"background-color: {ON_COLOR}; color: white;"
                 f"border: 1px solid {ON_BORDER}; border-radius: 6px;"
                 "font: bold 10px;")

InputStyleOff =  ("background-color: palette(alternate-base); color: palette(button-text);"
                  "border: 1px solid palette(mid); border-radius: 6px;"
                  "font: 10px;")
