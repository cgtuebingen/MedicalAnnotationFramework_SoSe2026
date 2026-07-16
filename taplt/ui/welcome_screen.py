import os

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy, QPushButton, QVBoxLayout
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt, Signal
from taplt import source_directory
from taplt.utils.stylesheets import BASE_FONT_SIZE


class WelcomeScreen(QWidget):

    sNewProject = Signal()
    sOpenProject = Signal()


    def __init__(self):
        super().__init__()

        icon_path = os.path.join(source_directory, 'icons', 'logo2.png').replace("\\", "/")
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
        
        # Buttons
        self.new_project_button = QPushButton("Create New Project")
        self.open_project_button = QPushButton("Open Project")

        self.new_project_button.setFixedWidth(220)
        self.open_project_button.setFixedWidth(220)
 
        self.new_project_button.setCursor(Qt.PointingHandCursor)
        self.open_project_button.setCursor(Qt.PointingHandCursor)
 
        self.new_project_button.clicked.connect(self.sNewProject.emit)
        self.open_project_button.clicked.connect(self.sOpenProject.emit)


        # Layout
        # Logo + Titel
        top_row = QHBoxLayout()
        top_row.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        top_row.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        top_row.setSpacing(20)
        top_row.setContentsMargins(0, 0, 0, 0)

        button_col = QVBoxLayout()
        button_col.addWidget(self.new_project_button, alignment=Qt.AlignCenter)
        button_col.addWidget(self.open_project_button, alignment=Qt.AlignCenter)
        button_col.setSpacing(10)
        button_col.setContentsMargins(0, 0, 0, 0)


        main_layout = QVBoxLayout()
        main_layout.addLayout(top_row)
        main_layout.addWidget(self.subtitle_label)
        main_layout.addLayout(button_col)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignCenter)

        self.setLayout(main_layout)

    def resizeEvent(self, event):
        """Logo dynamisch skalieren."""
        w = self.width()
        target_width = max(80, min(0.12 * w, 150))

        pixmap = QPixmap(os.path.join(source_directory, 'icons', 'logo2.png'))
        scaled = pixmap.scaledToWidth(int(target_width), Qt.SmoothTransformation)
        self.icon_label.setPixmap(scaled)

        super().resizeEvent(event)

