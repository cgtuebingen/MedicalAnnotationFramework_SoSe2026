import argparse
import sys

from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase
from taplt.src.main_logic import MainLogic
from taplt.utils.stylesheets import BASE_FONT_SIZE, sync_theme_with_system


def main(_args):
    app = QApplication(sys.argv)
    # Set global application font size
    font_file = Path(__file__).resolve().parent / "fonts" / "InterVariable.ttf"

    font_id = QFontDatabase.addApplicationFont(str(font_file))

    if font_id == -1:
        raise RuntimeError(f"Failed to load application font: {font_file}")
    
    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    global_font = QFont(font_family, BASE_FONT_SIZE)
    app.setFont(global_font)

    sync_theme_with_system()
    main_logic = MainLogic()  # the labeling window

    def on_scheme_changed(_scheme):
        sync_theme_with_system()
        main_logic.main_window.refresh_theme()

    app.styleHints().colorSchemeChanged.connect(on_scheme_changed)
    sys.exit(app.exec())


if __name__ == "__main__":
    # Add arguments to argument parser
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)
