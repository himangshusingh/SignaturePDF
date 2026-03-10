from PyQt6.QtWidgets import QWidget, QCheckBox
from PyQt6.QtCore import Qt, QRectF, QPropertyAnimation, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None, bg_color="#383842", circle_color="#A3A3A8", active_color="#605DE6", active_circle="#FFFFFF"):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._position = 0
        
        self.bg_color = bg_color
        self.circle_color = circle_color
        self.active_color = active_color
        self.active_circle = active_circle
        
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setDuration(150)
        
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
        if value:
            self.animation.setEndValue(1.0)
        else:
            self.animation.setEndValue(0.0)
        self.animation.start()

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dimensions
        w = 36
        h = 20
        y = (self.height() - h) // 2
        
        rect = QRectF(0, y, w, h)
        
        # Colors
        bg = QColor(self.active_color if self.isChecked() else self.bg_color)
        handle = QColor(self.active_circle if self.isChecked() else self.circle_color)
        
        # Track
        p.setBrush(bg)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, h / 2, h / 2)
        
        # Handle position based on animation state
        handle_x = 2 + self._position * (w - h)
        handle_rect = QRectF(handle_x, y + 2, h - 4, h - 4)
        
        p.setBrush(handle)
        p.drawEllipse(handle_rect)
        
        # Draw label text
        p.setPen(QColor(self.palette().color(self.foregroundRole())))
        font_rect = self.fontMetrics().boundingRect(self.text())
        p.drawText(w + 8, (self.height() + font_rect.height()) // 2 - 2, self.text())
