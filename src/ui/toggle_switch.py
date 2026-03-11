from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import Qt, QRectF, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen


class ToggleSwitch(QCheckBox):
    """Modern pill-shaped toggle switch matching the mockup design."""

    def __init__(self, parent=None,
                 bg_color="#131318",
                 border_color="rgba(255,255,255,0.07)",
                 circle_color="#6b6880",
                 active_color="#7c5cfc",
                 active_circle="#FFFFFF"):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._position = 0.0

        self.bg_color = bg_color
        self.border_color_str = border_color
        self.circle_color = circle_color
        self.active_color = active_color
        self.active_circle = active_circle

        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setDuration(200)

        self.stateChanged.connect(self.start_animation)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def start_animation(self, value):
        self.animation.stop()
        self.animation.setEndValue(1.0 if value else 0.0)
        self.animation.start()

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self.text()) if self.text() else 0
        total_width = 36 + (8 + text_width if text_width else 0)
        return QSize(total_width, max(22, fm.height() + 4))

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track dimensions
        w = 36
        h = 20
        y = (self.height() - h) // 2

        track_rect = QRectF(0, y, w, h)

        # Interpolate background color
        if self.isChecked() or self._position > 0:
            bg = QColor(self.active_color)
        else:
            bg = QColor(self.bg_color)

        # Draw track
        p.setBrush(bg)

        # Border
        if not self.isChecked() and self._position == 0:
            border_pen = QPen(QColor(255, 255, 255, 18))  # subtle border when off
            border_pen.setWidthF(1.0)
            p.setPen(border_pen)
        else:
            p.setPen(Qt.PenStyle.NoPen)

        p.drawRoundedRect(track_rect, h / 2, h / 2)

        # Handle
        handle_diameter = 14
        handle_margin = 3
        handle_x = handle_margin + self._position * (w - handle_diameter - handle_margin * 2)
        handle_y = y + (h - handle_diameter) / 2

        handle_color = QColor(self.active_circle) if self.isChecked() or self._position > 0.5 else QColor(self.circle_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(handle_color)
        p.drawEllipse(QRectF(handle_x, handle_y, handle_diameter, handle_diameter))

        # Draw text label if present
        if self.text():
            p.setPen(QColor(self.palette().color(self.foregroundRole())))
            text_x = w + 8
            text_y = (self.height() + self.fontMetrics().ascent() - self.fontMetrics().descent()) // 2
            p.drawText(text_x, text_y, self.text())

        p.end()
