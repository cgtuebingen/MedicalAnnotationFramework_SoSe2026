import os

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt
from taplt import source_directory
from taplt.utils.stylesheets import BASE_FONT_SIZE


class WelcomeScreen(QWidget):

    def __init__(self):
        super().__init__()

        icon_path = os.path.join(source_directory, 'icons', 'logo.png').replace("\\", "/")
        pixmap = QPixmap(icon_path)

        # Widget für Logo
        self.icon_label = QLabel()
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Name
        self.title_label = QLabel("All-Purpose Labeling Tool")
        self.title_label.setFont(QFont("Oswald", BASE_FONT_SIZE + 12, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignLeft)

        # Untertitel
        self.subtitle_label = QLabel("Create or open a project to get started")
        self.subtitle_label.setFont(QFont("Oswald", BASE_FONT_SIZE + 2, QFont.Weight.Bold))
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Layout
        # Logo + Titel
        top_row = QHBoxLayout()
        top_row.addWidget(self.icon_label)
        top_row.addWidget(self.title_label)
        top_row.setSpacing(20)
        top_row.setContentsMargins(0, 0, 0, 0)

        main_layout = QHBoxLayout()
        main_layout.addLayout(top_row)
        main_layout.addWidget(self.subtitle_label)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignCenter)

        self.setLayout(main_layout)

        def resizeEvent(self, event):
            """Logo dynamisch skalieren."""
            w = self.width()
            target_width = max(120, min(0.22 * w, 300))

            pixmap = QPixmap(os.path.join(source_directory, 'icons', 'logo.png'))
            scaled = pixmap.scaledToWidth(int(target_width), Qt.SmoothTransformation)
            self.icon_label.setPixmap(scaled)

            super().resizeEvent(event)

