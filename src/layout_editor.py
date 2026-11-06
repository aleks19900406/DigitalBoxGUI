"""The user can select groups of controls, drag them to the position he wants, rename or delete (hide) them."""
import json
import re

from PyQt6.QtCore import QEvent, QRect, QTimer, Qt
from PyQt6.QtGui import QColor, QCursor, QPainter, QPen
from PyQt6.QtWidgets import QAbstractButton, QInputDialog, QLabel, QMessageBox, QPushButton, QWidget

from .box_marks import (create_box_mark, list_box_marks, load_box_mark, set_box_mark_value, valid_box_mark_name,
                        widget_mark)
from .compact_layout import compact_layout, compact_layout_wanted
from .paths import APPLICATION_ROOT
from .scaling import MIN_WINDOW_WIDTH, fit_window_to_screen
from .session import device_key
from .styles import ButtonStyleOff2, ButtonStyleOn, ButtonStyleOn2

LAYOUT_FILE = APPLICATION_ROOT / "box_layout.json"
GRID = 5
# margin around the used area of the box and the smallest area (design pixels)
CROP_MARGIN = 10
CROP_MIN_HEIGHT = 120
# the window size is saved this long after the last resize
RESIZE_SAVE_DELAY_MS = 500
# digital potentiometers are arranged automatically, the title label switches with the heater systems
NOT_MOVABLE = re.compile(r"^(digital_pot|PotMin|PotMax|lcdNumber_digital_pot|labelDigitalPot)\d+$|^label_marks_2$")
EDITOR_BUTTONS = ("editLayoutButton", "resetLayoutButton")
EDITOR_WIDGETS = ("layoutOverlay",)
POT_PREFIXES = ("digital_pot", "PotMin", "PotMax", "lcdNumber_digital_pot", "labelDigitalPot")
POT_WIDGET = re.compile(r"^(?:digital_pot|PotMin|PotMax|lcdNumber_digital_pot|labelDigitalPot)(\d+)$")
POT_OVERLAP_TOLERANCE = 5
# the editor buttons can be moved but not deleted
NOT_DELETABLE = EDITOR_BUTTONS
# texts that must not be renamed: BOX CONNECT / SELECT MARKS / SAVE DATA and the ADDITIONAL FUNCTIONS buttons
NOT_RENAMEABLE = ("label_connect", "label_marks", "label_saveFile", "warningMessageAddFunction",
                  "ButtonHusaModel", "ButtonPyroSystem", "ButtonAutomation", "ButtonG800", "ButtonBIO24",
                  "ConnectToDevice", "ButtonCreateAutoTest", "RefreshingConnection", "startStopSaving", "on_off")
# the mouse must move this far (design pixels) before a press on an editor button becomes a drag
CLICK_DRAG_DISTANCE = 10


def _read_layout_file():
    try:
        with open(LAYOUT_FILE, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def read_layout(device=None):
    """Returns (positions, hidden, sizes): {name: (x, y)}, the set of deleted control names,
    {"full": (width, height)} window size set by the user.
    The layout arranged for the device (its IP) when there is one, otherwise the default layout."""
    data = _read_layout_file()
    devices = data.get("devices")
    if device and isinstance(devices, dict) and isinstance(devices.get(device), dict):
        data = devices[device]
    positions = {name: (int(pos[0]), int(pos[1])) for name, pos in data.get("positions", {}).items()
                 if isinstance(pos, (list, tuple)) and len(pos) == 2}
    sizes = {key: (int(size[0]), int(size[1])) for key, size in data.get("window_sizes", {}).items()
             if key == "full" and isinstance(size, (list, tuple)) and len(size) == 2
             and size[0] > 0 and size[1] > 0}
    return positions, {str(name) for name in data.get("hidden", [])}, sizes


def write_layout(positions, hidden, sizes, device=None):
    """Save the layout of the device (its IP); without a device the default layout is saved."""
    layout = {"positions": {name: list(pos) for name, pos in positions.items()},
              "hidden": sorted(hidden),
              "window_sizes": {key: list(size) for key, size in sizes.items()}}
    data = _read_layout_file()
    if device:
        devices = data.get("devices")
        data["devices"] = devices = devices if isinstance(devices, dict) else {}
        devices[device] = layout
    else:
        data.update(layout)
    try:
        with open(LAYOUT_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
    except OSError:
        pass


class SelectionOverlay(QWidget):
    """Transparent layer above the form that draws the selection (it does not take any mouse events)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("layoutOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.selected = []
        self.band = None
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor("#2563eb"), 2, Qt.PenStyle.DashLine))
        for widget in self.selected:
            painter.drawRect(widget.geometry().adjusted(-2, -2, 2, 2))
        if self.band is not None:
            painter.setBrush(QColor(37, 99, 235, 40))
            painter.drawRect(self.band)


class LayoutEditMixin:
    def setup_layout_editor(self):
        self.custom_positions, self.hidden_controls, self.window_sizes = read_layout()
        self._loading_layout = False
        self._applied_size = None
        self._snapping = False
        self._hidden_prev_visible = {}
        self.layout_edit = False
        self._drag = None
        self._button_press = None
        self._band = None
        self._selected = []
        self._label_defaults = {}
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(RESIZE_SAVE_DELAY_MS)
        self._resize_timer.timeout.connect(self._remember_window_size)
        self.layoutOverlay = SelectionOverlay(self.content_widget)
        self.editLayoutButton = self._edit_button(
            "editLayoutButton", "EDIT LAYOUT", (1415, 65, 111, 38),
            "Select controls with the mouse and drag them to the position you want, double click renames a text/button")
        self.editLayoutButton.clicked.connect(lambda: self.set_layout_edit(not self.layout_edit))
        self.resetLayoutButton = self._edit_button(
            "resetLayoutButton", "RESET LAYOUT", (1415, 28, 111, 34),
            "Return all controls and the window to the default position and size and show deleted controls "
            "(selected controls are deleted with the Delete key)")
        self.resetLayoutButton.clicked.connect(self.reset_layout)
        self.custom_positions, self.hidden_controls, self.window_sizes = self._starting_layout(
            self.custom_positions, self.hidden_controls, self.window_sizes)
        self.content_widget.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.content_widget.installEventFilter(self)

    def _starting_layout(self, positions, hidden, sizes):
        """Small screen: the compact layout until the user arranges the box (EDIT LAYOUT) himself."""
        if positions or hidden or not compact_layout_wanted():
            return positions, hidden, sizes
        compact_positions, compact_hidden = compact_layout(self)
        return compact_positions, compact_hidden, {}

    def _save_layout(self):
        """Save the layout for the connected device (the default layout when no device is connected)."""
        if not self._loading_layout:
            write_layout(self.custom_positions, self.hidden_controls, self.window_sizes,
                         device_key(self.session_connection))

    def load_device_layout(self, device):
        """A device was connected: the GUI is arranged like the last time this device was used (the default
        layout for a new device)."""
        positions, hidden, sizes = read_layout(device)
        self._loading_layout = True  # nothing of the previous layout may be saved for this device
        try:
            if self.layout_edit:
                self.set_layout_edit(False)
            self.release_deleted()
            self.restore_default_positions()
            self.custom_positions, self.hidden_controls, self.window_sizes = self._starting_layout(
                positions, hidden, sizes)
            self.io_show_all = False
            self._set_selection([])
            self.apply_layout()
        finally:
            self._loading_layout = False

    def crop_rect(self, full):
        """Area of the visible controls with a margin: the empty space of removed controls is not shown."""
        rect = QRect()
        for child in self.content_widget.children():
            if (isinstance(child, QWidget) and not child.isHidden() and child.objectName() not in EDITOR_WIDGETS
                    and child.width() > 0 and child.height() > 0
                    and not (self._is_blank_label(child) and not full.contains(child.geometry()))):
                rect = rect.united(child.geometry())
        if rect.isNull():
            return full
        rect.adjust(-CROP_MARGIN, -CROP_MARGIN, CROP_MARGIN, CROP_MARGIN)
        width = max(rect.width(), MIN_WINDOW_WIDTH)
        height = max(rect.height(), CROP_MIN_HEIGHT)
        rect = QRect(rect.x() - (width - rect.width()) // 2, rect.y() - (height - rect.height()) // 2, width, height)
        # shift the (enlarged) area back into the form, then cut it to the form
        rect.moveLeft(max(full.left(), min(rect.left(), full.right() + 1 - rect.width())))
        rect.moveTop(max(full.top(), min(rect.top(), full.bottom() + 1 - rect.height())))
        return rect.intersected(full)

    @staticmethod
    def _is_blank_label(widget):
        """Empty label without picture or style (it is drawn only when the application sets a text)."""
        return (isinstance(widget, QLabel) and not widget.text() and not widget.styleSheet()
                and (widget.pixmap() is None or widget.pixmap().isNull()))

    def pot_overlaps_controls(self, index):
        """True when a visible control (or an editor button) lies over the area of digital potentiometer `index`."""
        rect = QRect()
        for prefix in POT_PREFIXES:
            rect = rect.united(getattr(self, f"{prefix}{index}").geometry())
        # the default headings above the sliders touch this area by a pixel: ignore a small border
        rect = rect.adjusted(POT_OVERLAP_TOLERANCE, POT_OVERLAP_TOLERANCE, -POT_OVERLAP_TOLERANCE, -POT_OVERLAP_TOLERANCE)
        for child in self._movable_widgets():
            if child.objectName() in EDITOR_BUTTONS or (not child.isHidden() and not self._is_blank_label(child)):
                if child.geometry().intersects(rect):
                    return True
        return False

    def _fit_window_to_view(self, scale):
        """Window size for the shown area at the given scale (no empty bars around the content)."""
        view = self.scaled_view
        rect = view.view_rect
        delta = self.size() - view.viewport().size()
        self._snapping = True
        fit_window_to_screen(self, round(rect.width() * scale) + delta.width(),
                             round(rect.height() * scale) + delta.height())
        self._snapping = False

    def apply_window_size(self, width, height):
        """Start / device change: shown area and window size (the one the user set, otherwise the default)."""
        full = QRect(0, 0, width, height)
        rect = full if self.layout_edit else self.crop_rect(full)
        self.scaled_view.set_design_size(width, height, rect)
        if self.isMaximized() or self.isFullScreen():
            return
        width, height = self.window_sizes.get("full", (rect.width(), rect.height()))
        # compact layout without a saved size: as large as the screen allows
        fit_window_to_screen(self, width, height, enlarge=compact_layout_wanted() and "full" not in self.window_sizes)
        self._applied_size = (self.width(), self.height())

    def change_view_area(self):
        """EDIT LAYOUT on/off or controls moved/removed: the window keeps the scale, so it shrinks (grows)
        by the empty space that disappeared (appeared)."""
        view = self.scaled_view
        full = QRect(0, 0, self.content_widget.width(), self.content_widget.height())
        if self.layout_edit and compact_layout_wanted():
            return  # small screen: the window and the scale stay as they are while editing
        rect = full if self.layout_edit else self.crop_rect(full)
        if rect == view.view_rect:
            return
        scale = view.scale_factor()
        view.set_design_size(full.width(), full.height(), rect)
        if self.isMaximized() or self.isFullScreen():
            return
        self._fit_window_to_view(scale)
        self._applied_size = (self.width(), self.height())
        if not self.layout_edit:
            self.window_sizes["full"] = self._applied_size
            self._save_layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_resize_timer") and not self._snapping:
            self._resize_timer.start()

    def _remember_window_size(self):
        """The user changed the window size by hand: remove the empty bars around the content and save the size."""
        if (self.isMaximized() or self.isFullScreen() or self.isMinimized() or not self.isVisible()
                or self.layout_edit):
            return
        view = self.scaled_view
        rect = view.view_rect
        scale = view.scale_factor()
        delta = self.size() - view.viewport().size()
        if (abs(round(rect.width() * scale) + delta.width() - self.width()) > 1
                or abs(round(rect.height() * scale) + delta.height() - self.height()) > 1):
            self._fit_window_to_view(scale)
        size = (self.width(), self.height())
        if size == self._applied_size:
            return
        self._applied_size = size
        self.window_sizes["full"] = size
        self._save_layout()

    def _edit_button(self, name, text, rect, tip):
        button = QPushButton(text, self.content_widget)
        button.setObjectName(name)
        button.setGeometry(*rect)
        button.setStyleSheet(ButtonStyleOff2)
        button.setToolTip(tip)
        button.hide()
        return button

    def update_edit_buttons(self):
        self.editLayoutButton.setVisible(True)
        self.resetLayoutButton.setVisible(self.layout_edit)

    def _movable_widgets(self):
        return [child for child in self.content_widget.children()
                if isinstance(child, QWidget) and child.objectName()
                and child.objectName() not in EDITOR_WIDGETS and not NOT_MOVABLE.match(child.objectName())]

    def _selectable_widgets(self):
        """Movable controls, the digital potentiometers and the DIGITAL INPUT title (deleted but not moved)."""
        return self._movable_widgets() + [self.label_marks_2] + [getattr(self, f"{prefix}{index}")
                                                                 for prefix in POT_PREFIXES for index in range(6)]

    def _selection_group(self, widget):
        """A digital potentiometer is selected as a whole (slider, limits, display and name)."""
        match = POT_WIDGET.match(widget.objectName())
        if match is None:
            return [widget]
        return [getattr(self, f"{prefix}{match.group(1)}") for prefix in POT_PREFIXES]

    def _start_drag(self, origin):
        starts = {w: w.pos() for w in self._selected if not NOT_MOVABLE.match(w.objectName())}
        self._drag = (origin, starts) if starts else None

    def capture_default_positions(self):
        """Remember the default position of every movable control (before the custom positions are applied)."""
        if not hasattr(self, "_default_positions"):
            self._default_positions = {widget.objectName(): widget.pos() for widget in self._movable_widgets()}

    def apply_custom_positions(self):
        for name, (x, y) in self.custom_positions.items():
            widget = getattr(self, name, None)
            if isinstance(widget, QWidget):
                widget.move(x, y)
        for name in self.hidden_controls:
            widget = getattr(self, name, None)
            if isinstance(widget, QWidget) and not POT_WIDGET.match(name):  # sliders: see update_digital_pot_visibility
                self._hide_widget(widget)

    def _hide_widget(self, widget):
        name = widget.objectName()
        if name not in self._hidden_prev_visible:
            self._hidden_prev_visible[name] = not widget.isHidden()
        widget.installEventFilter(self)  # other code of the application may try to show it again
        widget.hide()

    def release_deleted(self):
        """Deleted controls are visible again (RESET LAYOUT / another device)."""
        for name, visible in self._hidden_prev_visible.items():
            widget = getattr(self, name, None)
            if isinstance(widget, QWidget):
                widget.removeEventFilter(self)
                widget.setVisible(visible)
        self._hidden_prev_visible = {}

    def restore_default_positions(self):
        """Controls moved by the user go back to their default position."""
        for name in self.custom_positions:
            widget = getattr(self, name, None)
            if isinstance(widget, QWidget) and name in self._default_positions:
                widget.move(self._default_positions[name])

    def set_layout_edit(self, enabled):
        self.layout_edit = enabled
        self._drag = None
        self._button_press = None
        self._band = None
        self._set_selection([])
        for widget in self._selectable_widgets():
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, enabled)
        self.content_widget.setCursor(QCursor(Qt.CursorShape.SizeAllCursor) if enabled else QCursor())
        self.layoutOverlay.setGeometry(self.content_widget.rect())
        self.layoutOverlay.setVisible(enabled)
        if enabled:
            self.layoutOverlay.raise_()
            self.content_widget.setFocus()
        self.editLayoutButton.setText("DONE" if enabled else "EDIT LAYOUT")
        self.editLayoutButton.setStyleSheet(ButtonStyleOn2 if enabled else ButtonStyleOff2)
        self.update_edit_buttons()
        if not enabled and getattr(self, "_crop_ready", False):
            self.update_digital_pot_visibility()  # sliders under moved controls are hidden (calls change_view_area)
        elif getattr(self, "_crop_ready", False):
            self.update_digital_pot_visibility()  # all sliders, inputs and outputs are shown while editing
            self.change_view_area()

    def reset_layout(self):
        self.release_deleted()
        self.restore_default_positions()
        self.custom_positions = {}
        self.hidden_controls = set()
        self.window_sizes.pop("full", None)
        self.custom_positions, self.hidden_controls, _ = self._starting_layout({}, set(), {})
        self._save_layout()
        self._set_selection([])
        self.apply_layout()
        self.io_show_all = True  # all digital inputs and outputs, not only the named ones in the box marks
        self.update_digital_pot_visibility()

    def delete_selected(self):
        for widget in self._selected:
            name = widget.objectName()
            if name in NOT_DELETABLE:
                continue
            match = POT_WIDGET.match(name)
            if match:  # the whole slider is deleted, the remaining ones move together
                self.hidden_controls.add(f"digital_pot{match.group(1)}")
                continue
            self.hidden_controls.add(name)
            self._hide_widget(widget)
        self._set_selection([])
        self.update_digital_pot_visibility()
        self._save_layout()

    def _set_selection(self, widgets):
        self._selected = list(widgets)
        self.layoutOverlay.selected = self._selected
        self.layoutOverlay.update()

    @staticmethod
    def _renameable(widget):
        name = widget.objectName()
        if not name or name in NOT_DELETABLE or name in NOT_RENAMEABLE or name in EDITOR_WIDGETS:
            return False
        return isinstance(widget, QAbstractButton) or (isinstance(widget, QLabel) and bool(widget.text()))

    def _renameable_at(self, pos):
        for child in reversed(self.content_widget.children()):
            if (isinstance(child, QWidget) and child.isVisible() and child.geometry().contains(pos)
                    and self._renameable(child)):
                return child
        return None

    def rename_widget(self, widget):
        """Ask for a new text of the widget and save it into the json of the selected box marks."""
        box_mark = self.session_box_mark
        if not box_mark:
            self.create_new_box_mark()
            return
        name = widget.objectName()
        section, index, default = widget_mark(name)
        text, accepted = QInputDialog.getText(self, "Rename", f"New text ({name}):", text=widget.text())
        text = text.strip()
        if not accepted or text == widget.text() or (not text and default is None):
            return
        try:
            set_box_mark_value(box_mark, section, text, index)
            self.box_mark_data = load_box_mark(box_mark)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Rename", f"The name could not be saved in {box_mark}.json:\n{error}")
            return
        if section == "LABELS":
            self._label_defaults.setdefault(name, widget.text())
        elif section == "DIGITAL_POT":
            names = self.box_mark_data.get(section, [])
            self.active_pots = [pot for pot in range(6) if pot < len(names) and names[pot]]  # sliders shown after DONE
        elif section.startswith("AUTO") and isinstance(getattr(self, f"param_{section.lower()}", None), list):
            getattr(self, f"param_{section.lower()}")[0] = text
        widget.setText(text or default)

    def create_new_box_mark(self):
        """No BOX MARKS selected: ask for the name of new (empty) box marks and select them."""
        name, accepted = QInputDialog.getText(
            self, "New BOX MARKS", "BOX MARKS are not selected. Name of the new BOX MARKS:")
        name = name.strip()
        if not accepted or not name:
            return
        if not valid_box_mark_name(name):
            QMessageBox.warning(self, "New BOX MARKS", f'"{name}" can not be used as a file name.')
            return
        if name in list_box_marks():
            QMessageBox.warning(self, "New BOX MARKS", f'BOX MARKS "{name}" already exist: select them in the list.')
            return
        try:
            create_box_mark(name)
        except OSError as error:
            QMessageBox.warning(self, "New BOX MARKS", f"{name}.json could not be created:\n{error}")
            return
        if self.BoxMarks.findText(name) < 0:
            self.BoxMarks.addItem(name)
        self.BoxMarks.setCurrentText(name)
        self.BoxMarks.setStyleSheet(ButtonStyleOn)
        self.session_box_mark = name
        self.box_mark_data = load_box_mark(name)
        self.save_session()

    def apply_box_mark_labels(self, labels):
        """Texts of the LABELS section of the box marks (the ones of the previous box marks are restored)."""
        for name, text in list(self._label_defaults.items()):
            widget = getattr(self, name, None)
            if name not in labels and isinstance(widget, QWidget):
                widget.setText(text)
                del self._label_defaults[name]
        for name, text in labels.items():
            widget = getattr(self, name, None)
            if name not in NOT_RENAMEABLE and isinstance(widget, QWidget) and hasattr(widget, "setText"):
                self._label_defaults.setdefault(name, widget.text())
                widget.setText(text)

    def _widget_at(self, pos):
        for child in reversed(self._selectable_widgets()):
            if child.isVisible() and child.geometry().contains(pos):
                return child
        return None

    def _drag_selection(self, pos):
        origin, starts = self._drag
        content = self.content_widget
        dx = round((pos.x() - origin.x()) / GRID) * GRID
        dy = round((pos.y() - origin.y()) / GRID) * GRID
        # the whole group stays inside the form
        dx = max(-min(p.x() for p in starts.values()),
                 min(dx, content.width() - max(p.x() + w.width() for w, p in starts.items())))
        dy = max(-min(p.y() for p in starts.values()),
                 min(dy, content.height() - max(p.y() + w.height() for w, p in starts.items())))
        for widget, start in starts.items():
            widget.move(start.x() + dx, start.y() + dy)
        self.layoutOverlay.update()

    def _mouse_press(self, event):
        pos = event.position().toPoint()
        widget = self._widget_at(pos)
        extend = bool(event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier))
        self.content_widget.setFocus()
        if widget is not None and widget.objectName() in EDITOR_BUTTONS and not extend:
            # click or drag: decided when the mouse moves or is released (the selection stays as it is)
            self._button_press = (widget, pos)
        elif widget is not None and extend:
            selection = list(self._selected)
            group = self._selection_group(widget)
            if widget in selection:
                selection = [w for w in selection if w not in group]
            else:
                selection += [w for w in group if w not in selection]
            self._set_selection(selection)
        elif widget is not None:
            if widget not in self._selected:
                self._set_selection(self._selection_group(widget))
            self._start_drag(pos)
        else:
            self._band = (pos, list(self._selected) if extend else [])
            if not extend:
                self._set_selection([])

    def _mouse_move(self, event):
        pos = event.position().toPoint()
        if self._button_press and (pos - self._button_press[1]).manhattanLength() >= CLICK_DRAG_DISTANCE:
            button, origin = self._button_press
            self._button_press = None
            if button not in self._selected:
                self._set_selection([button])
            self._start_drag(origin)
        if self._drag:
            self._drag_selection(pos)
        elif self._band:
            origin, base = self._band
            rect = QRect(origin, pos).normalized()
            hit = []
            for w in self._selectable_widgets():
                if w.isVisible() and w.geometry().intersects(rect):
                    hit += [g for g in self._selection_group(w) if g not in hit]
            self._set_selection(base + [w for w in hit if w not in base])
            self.layoutOverlay.band = rect

    def _mouse_release(self):
        if self._button_press:
            button = self._button_press[0]
            self._button_press = None
            button.click()
            return
        if self._drag:
            for widget in self._drag[1]:
                self.custom_positions[widget.objectName()] = (widget.x(), widget.y())
            self._save_layout()
        self._drag = None
        self._band = None
        self.layoutOverlay.band = None
        self.layoutOverlay.update()

    def eventFilter(self, obj, event):
        kind = event.type()
        if (kind == QEvent.Type.Show and obj is not self.content_widget
                and obj.objectName() in self.hidden_controls):
            QTimer.singleShot(0, obj.hide)
        elif obj is self.content_widget and self.layout_edit:
            if kind == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._mouse_press(event)
                return True
            if kind == QEvent.Type.MouseMove:
                self._mouse_move(event)
                return True
            if kind == QEvent.Type.MouseButtonRelease:
                self._mouse_release()
                return True
            if kind == QEvent.Type.MouseButtonDblClick and event.button() == Qt.MouseButton.LeftButton:
                widget = self._renameable_at(event.position().toPoint())
                if widget is not None:
                    self.rename_widget(widget)
                return True
            if kind == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_F2 and len(self._selected) == 1 and self._renameable(self._selected[0]):
                    self.rename_widget(self._selected[0])
                    return True
                if event.key() == Qt.Key.Key_Delete:
                    self.delete_selected()
                    return True
                if event.key() == Qt.Key.Key_Escape:
                    self._set_selection([])
                    return True
        return super().eventFilter(obj, event)
