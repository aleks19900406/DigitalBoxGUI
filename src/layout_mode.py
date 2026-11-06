from PyQt6.QtCore import QRect

from .compact_layout import (EDITOR_BUTTONS, compact_layout_wanted, enlarge_buttons, enlarge_connection,
                             enlarge_pot_texts, shrink_pots)
from .scaling import make_scalable

FULL_WINDOW_WIDTH = 1530
FULL_WINDOW_HEIGHT = 1050

# separator lines of the form are not shown (they overlap the text)
SEPARATOR_LINES = ('line',) + tuple(f'line_{index}' for index in range(2, 13))

# the header (connect / marks / save) moves left to free the right edge for the buttons
FULL_HEADER_SHIFT = -50
FULL_HEADER = (
    'label_connect', 'BoxConnect', 'connectBar',
    'label_marks', 'BoxMarks', 'label_saveFile', 'ExcelFile', 'label_connect_3', 'RefreshingConnection',
    'excelRefresh', 'label_connect_2', 'startStopSaving', 'ip_scanning')

# DIGITAL INPUT label geometry while a heater system is shown instead of the title
FULL_SYSTEMS_LABEL = QRect(10, 741, 610, 44)


class LayoutModeMixin:
    """The main window always shows the whole digital box; the user arranges it with EDIT LAYOUT."""

    def enable_screen_scaling(self):
        """The form uses fixed pixel positions: the whole content is scaled to the window (and the window to the screen)."""
        make_scalable(self, FULL_WINDOW_WIDTH, FULL_WINDOW_HEIGHT)

    def setup_layout_mode(self):
        for name in FULL_HEADER:
            widget = getattr(self, name)
            widget.move(widget.x() + FULL_HEADER_SHIFT, widget.y())
        self.backupSave.resize(240, self.backupSave.height())
        self.savingBar.resize(240, self.savingBar.height())
        self.servicesButton.setGeometry(1415, 106, 111, 30)
        self.update_gui.setGeometry(1415, 139, 111, 30)
        self.themeButton.setGeometry(1415, 172, 111, 30)
        if compact_layout_wanted():
            shrink_pots(self)
            enlarge_pot_texts(self)
            enlarge_connection(self)
            enlarge_buttons(self)
        self.setup_layout_editor()
        if compact_layout_wanted():
            enlarge_buttons(self, EDITOR_BUTTONS)
        self.apply_layout()

    def apply_layout(self):
        """The default positions plus the layout of the user (moved and deleted controls, window size)."""
        self._crop_ready = False
        self.capture_default_positions()
        self.apply_custom_positions()
        self.update_edit_buttons()
        self.update_digital_pot_visibility()
        title_shown = self.label_marks_2.text() == 'DIGITAL INPUT'
        self.label_marks_2.setGeometry(self.digital_input_label_geometry if title_shown
                                       else self.digital_input_systems_geometry)
        for name in SEPARATOR_LINES:
            getattr(self, name).setVisible(False)
        self.scaled_view.set_design_size(FULL_WINDOW_WIDTH, FULL_WINDOW_HEIGHT)
        self.apply_window_size(FULL_WINDOW_WIDTH, FULL_WINDOW_HEIGHT)
        self._crop_ready = True
