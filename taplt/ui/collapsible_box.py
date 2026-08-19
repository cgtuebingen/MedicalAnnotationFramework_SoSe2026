from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolButton, QSizePolicy
from PySide6.QtCore import Qt


class CollapsibleBox(QWidget):
    """A simple accordion-style section with a clickable header that shows/hides its content."""

    def __init__(self, title: str = "", parent=None, start_collapsed: bool = False):
        super().__init__(parent)

        self.toggle_button = QToolButton(self)
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(not start_collapsed)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow if not start_collapsed else Qt.ArrowType.RightArrow)
        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: rgb(186, 189, 182);
                font-weight: bold;
                padding: 4px;
                text-align: left;
            }
        """)
        self.toggle_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggle_button.clicked.connect(self._on_toggle)

        self.content_area = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_area.setVisible(not start_collapsed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

    def setContentWidget(self, widget: QWidget):
        """Places the given widget inside the collapsible content area."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        self.content_layout.addWidget(widget)

    def _on_toggle(self, checked: bool):
        self.content_area.setVisible(checked)
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)

    def set_collapsed(self, collapsed: bool):
        self.toggle_button.setChecked(not collapsed)
        self._on_toggle(not collapsed)