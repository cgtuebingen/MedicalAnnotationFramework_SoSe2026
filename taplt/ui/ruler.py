from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QFont, QPainter, QColor
from PySide6.QtCore import Qt 

from taplt.utils.stylesheets import FONT_SMALL

class RulerWidget(QWidget):

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


    LABEL_MARGIN = 5
    TICK_MARGIN = 2
    BOTTOM_MARGIN = 3
    MINOR_TICK_HEIGHT = 5
    MAJOR_TICK_HEIGHT = 10

    MAJOR_STEP = 50
    MINOR_TICKS_PER_SECTION = 5

    def __init__(self, orientation=HORIZONTAL, parent=None):
        super().__init__(parent)

        self.orientation = orientation

        self.zoom_factor = 1.0
        if self.orientation == self.HORIZONTAL:
            self.setFixedHeight(25)
        else:
            self.setFixedWidth(45)
        
        ruler_font = QFont(self.font())
        ruler_font.setPointSize(FONT_SMALL)
        self.setFont(ruler_font)


    def set_zoom(self, zoom: float):
        self.zoom_factor = zoom
        self.update()  # Trigger a repaint

    def paintEvent(self, event):
        painter = QPainter(self)

        pen = painter.pen()
        pen.setColor(QColor(95, 95, 95))
        pen.setWidth(1)
        painter.setPen(pen)

        # Draw the ruler background
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        # Draw the ruler ticks and labels based on orientation
        if self.orientation == self.HORIZONTAL:
            self._paint_horizontal(painter)
        else:
            self._paint_vertical(painter)

    def _paint_horizontal(self, painter: QPainter):
        ''' Paints the horizontal ruler on the top of the widget.'''
        fm = painter.fontMetrics()

        # Distance between major ticks in pixels, adjusted by zoom factor
        step = int(self.MAJOR_STEP * self.zoom_factor)

        x = 0
        value = 0

        while x < self.width():
            text = str(value)
            text_width = fm.horizontalAdvance(text)

            # Center the label above the tick mark, ensuring it doesn't go out of bounds
            text_x = max(2, int(x - text_width / 2))

            # Draw the label
            text_bottom = fm.height() - self.LABEL_MARGIN
            painter.drawText(text_x, text_bottom, text)

            # Draw the tick mark
            painter.drawLine(x, self.height() - self.BOTTOM_MARGIN - self.MAJOR_TICK_HEIGHT, x, self.height() - self.BOTTOM_MARGIN)

            # Draw smaller tick marks between the major ticks
            small_step = step / self.MINOR_TICKS_PER_SECTION

            for tick in range(1, self.MINOR_TICKS_PER_SECTION):
                small_x = x + tick * small_step

                painter.drawLine(
                    small_x,
                    self.height() - self.BOTTOM_MARGIN - self.MINOR_TICK_HEIGHT,
                    small_x,
                    self.height() - self.BOTTOM_MARGIN
                )

            x += step
            value += self.MAJOR_STEP

        # Draw the baseline at the bottom
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

    def _paint_vertical(self, painter: QPainter):
        ''' Paints the vertical ruler on the left side of the widget.'''
        fm = painter.fontMetrics()

        step = int(self.MAJOR_STEP * self.zoom_factor)

        y = 0
        value = 0

        while y < self.height():
            text = str(value)

            # Center the label to the left of the tick mark, ensuring it doesn't go out of bounds
            tick_x = self.width() - self.BOTTOM_MARGIN 
            text_width = fm.horizontalAdvance(text)
            text_x = max(2, tick_x - self.MAJOR_TICK_HEIGHT - self.LABEL_MARGIN - text_width)

            # Draw the label
            text_y = max(fm.ascent(), y + fm.ascent() - fm.height() / 2)
            painter.drawText(text_x, text_y, text)

            # Draw the tick mark
            painter.drawLine(self.width() - self.BOTTOM_MARGIN - self.MAJOR_TICK_HEIGHT, y, self.width() - self.BOTTOM_MARGIN, y)

            # Draw smaller tick marks between the major ticks
            small_step = step / self.MINOR_TICKS_PER_SECTION

            for tick in range(1, self.MINOR_TICKS_PER_SECTION):
                small_y = y + tick * small_step

                painter.drawLine(
                    self.width() - self.BOTTOM_MARGIN - self.MINOR_TICK_HEIGHT,
                    small_y,
                    self.width() - self.BOTTOM_MARGIN,
                    small_y
                )

            y += step
            value += self.MAJOR_STEP

        # Draw the baseline at the bottom
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)