"""Animated splash screen shown while the application windows are loading."""

from PyQt6.QtCore import QEventLoop, QPropertyAnimation, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen
from . import state
from .styles import ACCENT, THEMES, saved_theme


class SplashScreen(QSplashScreen):
    def __init__(self, steps):
        pixmap = QPixmap(460, 260)
        pixmap.fill(Qt.GlobalColor.transparent)
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.colors = THEMES.get(saved_theme(), THEMES["light"])
        self.steps = steps
        self.done = 0
        self.progress = 0.0
        self.shown_progress = 0.0
        self.angle = 0
        self.message = "Starting..."
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(25)
        self.show()
        self.process_events()

    def process_events(self):
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

    def animate(self):
        self.angle = (self.angle + 10) % 360
        self.shown_progress += (self.progress - self.shown_progress) * 0.25
        self.update()

    def advance(self, message):
        """Show the next loading step."""
        self.message = message
        self.progress = self.done / self.steps
        self.shown_progress = self.progress
        self.done += 1
        self.animate()
        self.repaint()
        self.process_events()

    def close_animated(self):
        """Fill the progress bar and fade the splash screen out."""
        self.message = "Ready"
        self.progress = 1.0
        self.animation = QPropertyAnimation(self, b"windowOpacity", self)
        self.animation.setDuration(400)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        QTimer.singleShot(250, self.animation.start)

    def mousePressEvent(self, event):
        pass

    def paintEvent(self, event):
        c = self.colors
        width = self.width()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QPen(QColor(c["border"]), 1))
        painter.setBrush(QColor(c["surface"]))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 14, 14)

        painter.setPen(QColor(c["title"]))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 30, width, 40), Qt.AlignmentFlag.AlignCenter, "DIGITAL BOX")
        painter.setPen(QColor(c["muted"]))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(QRectF(0, 68, width, 20), Qt.AlignmentFlag.AlignCenter, state.DIGITAL_BOX_VERSION)

        spinner = QRectF(width / 2 - 22, 105, 44, 44)
        pen = QPen(QColor(c["track"]), 5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(spinner)
        pen.setColor(QColor(ACCENT))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(spinner, -self.angle * 16, 100 * 16)

        bar = QRectF(50, 180, width - 100, 6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(c["track"]))
        painter.drawRoundedRect(bar, 3, 3)
        bar.setWidth(bar.width() * self.shown_progress)
        painter.setBrush(QColor(ACCENT))
        painter.drawRoundedRect(bar, 3, 3)

        painter.setPen(QColor(c["text"]))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(QRectF(0, 198, width, 30), Qt.AlignmentFlag.AlignCenter, self.message)
        painter.setPen(QColor(c["muted"]))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QRectF(0, 226, width, 20), Qt.AlignmentFlag.AlignCenter, "Starting takes about 20 s, please wait...")
