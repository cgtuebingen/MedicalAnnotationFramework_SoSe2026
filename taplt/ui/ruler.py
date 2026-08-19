from __future__ import annotations

from math import floor, log10

from PIL import Image
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QFont, QPainter, QColor
from PySide6.QtCore import Qt

from taplt.utils.stylesheets import FONT_SMALL


NICE_INTERVALS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]

PIXEL_CONTEXT = {
    "kind": "pixel",
    "unit": "px",
    "unit_per_pixel": 1.0,
    "label": "px",
}


def calculate_tick_interval(visible_span: float) -> float:
    """Return a nice step size for a ruler based on the visible span in the current unit."""
    if visible_span <= 0:
        return 1.0

    target_count = 5
    raw_step = visible_span / target_count
    magnitude = 10 ** floor(log10(raw_step)) if raw_step > 0 else 1.0
    normalized = raw_step / magnitude

    for nice in NICE_INTERVALS:
        if nice >= normalized:
            return nice * magnitude

    return NICE_INTERVALS[-1] * magnitude


def format_measurement_value(value: float, unit: str) -> str:
    """Formats the scalar value for the ruler using a compact label."""
    if unit == "px":
        return str(int(value))

    if unit == "mm":
        value = value / 1000.0

    if abs(value) >= 100:
        return f"{int(round(value))}"
    
    if abs(value) >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    
    return f"{value:.2f}".rstrip("0").rstrip(".")

def create_physical_context(unit_per_pixel: float) -> dict:
    """Creates a physical measurement context dictionary for the ruler."""
    return {
        "kind": "physical",
        "unit": "um",
        "unit_per_pixel": unit_per_pixel,
        "label": "µm",
    }

def read_image_metadata(filepath: str) -> dict:
    """Read DPI metadata from common image formats. Falls back to pixel-based display if no reliable physical data exists."""
    fallback = PIXEL_CONTEXT.copy()

    try:
        with Image.open(filepath) as img:
            info = img.info or {}
            dpi = info.get("dpi")
            if isinstance(dpi, (tuple, list)) and len(dpi) >= 2:
                x_dpi, y_dpi = float(dpi[0]), float(dpi[1])
            elif isinstance(dpi, (int, float)):
                x_dpi = y_dpi = float(dpi)
            else:
                x_dpi = y_dpi = 0.0

            if x_dpi > 0 and y_dpi > 0:
                avg_dpi = (x_dpi + y_dpi) / 2.0
                return create_physical_context(25400.0 / avg_dpi) # Convert DPI to micrometers per pixel 
    except Exception:
        pass

    return fallback


def read_slide_metadata(slide) -> dict:
    """Read the physical resolution metadata from OpenSlide if available."""
    fallback = PIXEL_CONTEXT.copy()

    if slide is None:
        return fallback

    properties = getattr(slide, "properties", {}) or {}

    def get_prop(*names):
        for name in names:
            value = properties.get(name)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    mpp_x = get_prop("openslide.mpp-x", "aperio.MPP")
    mpp_y = get_prop("openslide.mpp-y", "aperio.MPP")

    if mpp_x is None and mpp_y is None:
        return fallback

    if mpp_x is None:
        mpp_x = mpp_y
    if mpp_y is None:
        mpp_y = mpp_x

    if mpp_x <= 0 or mpp_y <= 0:
        return fallback

    avg_mpp = (mpp_x + mpp_y) / 2.0
    return create_physical_context(avg_mpp) 


class RulerWidget(QWidget):

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

    LABEL_MARGIN = 5
    TICK_MARGIN = 2
    BOTTOM_MARGIN = 3
    MINOR_TICK_HEIGHT = 5
    MAJOR_TICK_HEIGHT = 10
    MINOR_TICKS_PER_SECTION = 5

    def __init__(self, orientation=HORIZONTAL, parent=None):
        super().__init__(parent)

        self.orientation = orientation
        self.zoom_factor = 1.0
        self.ruler_context = PIXEL_CONTEXT.copy()

        if self.orientation == self.HORIZONTAL:
            self.setFixedHeight(25)
        else:
            self.setFixedWidth(45)

        ruler_font = QFont(self.font())
        ruler_font.setPointSize(FONT_SMALL)
        self.setFont(ruler_font)

    def set_measurement_context(self, context: dict):
        """Sets the measurement context of the ruler, including unit and scaling."""
        if not context:
            context = PIXEL_CONTEXT.copy()
        self.ruler_context = context
        self.update()

    def set_zoom(self, zoom: float):
        """Sets the zoom factor for the ruler, affecting how units are displayed."""
        self.zoom_factor = max(float(zoom), 1e-6)
        self.update()

    def _visible_span_in_units(self):
        """Calculates the visible span of the ruler in the current measurement unit."""
        #span_px = (self.width() if self.orientation == self.HORIZONTAL else self.height()) * self.zoom_factor
        size = (
            self.width()
            if self.orientation == self.HORIZONTAL 
            else self.height()
            )
        
        span_px = size / self.zoom_factor

        return span_px * float(self.ruler_context.get("unit_per_pixel", 1.0))

    def _tick_interval_in_units(self):
        """Calculates the tick interval in the current measurement unit based on the visible span."""
        interval = calculate_tick_interval(self._visible_span_in_units())

        if self.ruler_context.get("unit") == "px":
            interval = max(1.0, interval)

        return interval

    def _format_value(self, value: float) -> str:
        """Formats the scalar value for the ruler using a compact label."""
        unit = self.ruler_context.get("unit", "px")
        return format_measurement_value(value, unit)

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
        """Paints the horizontal ruler on the top of the widget."""
        fm = painter.fontMetrics()
        unit_per_pixel = float(self.ruler_context.get("unit_per_pixel", 1.0))
        step_in_units = self._tick_interval_in_units()
        step_in_pixels = (step_in_units / unit_per_pixel) * self.zoom_factor

        x = 0
        value = 0.0

        while x < self.width() + step_in_pixels:
            text = self._format_value(value)
            text_width = fm.horizontalAdvance(text)
            # # Center the label above the tick mark, ensuring it doesn't go out of bounds
            text_x = max(2, int(x - text_width / 2))

            # Draw the label
            text_bottom = fm.height() - self.LABEL_MARGIN
            painter.drawText(text_x, text_bottom, text)

            # Draw the tick mark
            painter.drawLine(x, self.height() - self.BOTTOM_MARGIN - self.MAJOR_TICK_HEIGHT, x, self.height() - self.BOTTOM_MARGIN)

            small_step = step_in_pixels / self.MINOR_TICKS_PER_SECTION
            for tick in range(1, self.MINOR_TICKS_PER_SECTION):
                small_x = x + tick * small_step
                painter.drawLine(
                    small_x,
                    self.height() - self.BOTTOM_MARGIN - self.MINOR_TICK_HEIGHT,
                    small_x,
                    self.height() - self.BOTTOM_MARGIN,
                )

            x += step_in_pixels
            value += step_in_units

        # Draw the baseline at the bottom
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

    def _paint_vertical(self, painter: QPainter):
        """Paints the vertical ruler on the left side of the widget."""
        fm = painter.fontMetrics()
        unit_per_pixel = float(self.ruler_context.get("unit_per_pixel", 1.0))
        step_in_units = self._tick_interval_in_units()
        step_in_pixels = (step_in_units / unit_per_pixel) * self.zoom_factor

        y = 0
        value = 0.0

        while y < self.height() + step_in_pixels:
            text = self._format_value(value)
            tick_x = self.width() - self.BOTTOM_MARGIN
            text_width = fm.horizontalAdvance(text)
            text_x = max(2, tick_x - self.MAJOR_TICK_HEIGHT - self.LABEL_MARGIN - text_width)

            # Draw the label
            text_y = max(fm.ascent(), y + fm.ascent() - fm.height() / 2)
            painter.drawText(text_x, text_y, text)

            # Draw the tick mark
            painter.drawLine(self.width() - self.BOTTOM_MARGIN - self.MAJOR_TICK_HEIGHT, y, self.width() - self.BOTTOM_MARGIN, y)

            small_step = step_in_pixels / self.MINOR_TICKS_PER_SECTION
            for tick in range(1, self.MINOR_TICKS_PER_SECTION):
                small_y = y + tick * small_step
                painter.drawLine(
                    self.width() - self.BOTTOM_MARGIN - self.MINOR_TICK_HEIGHT,
                    small_y,
                    self.width() - self.BOTTOM_MARGIN,
                    small_y,
                )

            y += step_in_pixels
            value += step_in_units

        # Draw the baseline at the bottom
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())