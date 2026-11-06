"""Uniform scaling of the fixed-pixel forms so the content always fits the window (any display size)."""
from PyQt6.QtCore import QRect, QRectF, Qt
from PyQt6.QtGui import QGuiApplication, QPainter, QPalette
from PyQt6.QtWidgets import (QDockWidget, QFrame, QGraphicsScene, QGraphicsView, QMenuBar, QStatusBar, QToolBar,
                             QWidget)

MIN_WINDOW_WIDTH = 320
# margins for the window frame and the taskbar
FRAME_WIDTH = 16
FRAME_HEIGHT = 40


class ScaledView(QGraphicsView):
    """Shows a widget with fixed design size and scales it (with fonts) to the size of the view."""

    def __init__(self, content, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setRenderHints(QPainter.RenderHint.TextAntialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.viewport().setBackgroundRole(QPalette.ColorRole.Window)
        self.setScene(QGraphicsScene(self))
        self.content = content
        self.proxy = self.scene().addWidget(content)
        self.view_rect = QRect(0, 0, max(1, content.width()), max(1, content.height()))

    def set_design_size(self, width, height, view_rect=None):
        """The content has the size width x height; only view_rect of it is shown (default: all of it)."""
        self.view_rect = view_rect or QRect(0, 0, width, height)
        self.content.setFixedSize(width, height)
        self.scene().setSceneRect(QRectF(self.view_rect))
        self._refit()

    def scale_factor(self):
        return min(self.viewport().width() / self.view_rect.width(),
                   self.viewport().height() / self.view_rect.height())

    def _refit(self):
        factor = self.scale_factor()
        if factor <= 0:
            return
        self.resetTransform()
        self.scale(factor, factor)
        self.centerOn(QRectF(self.view_rect).center())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refit()


def make_scalable(window, width, height):
    """Replace the central widget of a QMainWindow with a view that scales it to the window size."""
    content = window.takeCentralWidget()
    if content is None:
        # form loaded from a QWidget .ui: its widgets are direct children of the window
        content = QWidget()
        content.setObjectName('centralwidget')
        content.resize(width, height)
        for child in window.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            if isinstance(child, (QMenuBar, QStatusBar, QToolBar, QDockWidget)):
                continue
            visible = not child.isHidden()
            child.setParent(content)
            child.setVisible(visible)
    view = ScaledView(content, window)
    view.set_design_size(width, height)
    window.setCentralWidget(view)
    window.content_widget = content
    window.scaled_view = view
    window.setMinimumSize(MIN_WINDOW_WIDTH, round(MIN_WINDOW_WIDTH * height / width))
    fit_window_to_screen(window, width, height)
    return view


def fit_window_to_screen(window, width, height, x=None, y=None, enlarge=False):
    """Resize the window to the design size (aspect ratio kept), but never larger than the free screen area
    (enlarge: the window may be larger than the design size, up to the free screen area)."""
    # setGeometry() positions the client area: use client coordinates and keep the title bar on the screen
    client = window.geometry()
    frame = window.frameGeometry()
    x = client.x() if x is None else x
    y = client.y() if y is None else y
    screen = QGuiApplication.primaryScreen()
    if screen is not None:
        available = screen.availableGeometry()
        factor = min((available.width() - FRAME_WIDTH) / width, (available.height() - FRAME_HEIGHT) / height)
        if not enlarge:
            factor = min(1.0, factor)
        width = round(width * factor)
        height = round(height * factor)
        left_margin = client.x() - frame.x()
        top_margin = client.y() - frame.y()
        x = max(available.left() + left_margin, min(x, available.right() - width))
        y = max(available.top() + top_margin, min(y, available.bottom() - height))
    window.setGeometry(x, y, width, height)
