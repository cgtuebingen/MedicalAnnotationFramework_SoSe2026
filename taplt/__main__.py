import argparse
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from taplt.src.main_logic import MainLogic
from taplt.utils.stylesheets import BASE_FONT_SIZE


def main(_args):
    app = QApplication(sys.argv)
    # Set global application font size
    global_font = QFont()
    global_font.setPointSize(BASE_FONT_SIZE)
    app.setFont(global_font)
    _ = MainLogic()  # the labeling window
    sys.exit(app.exec())


if __name__ == "__main__":
    # Add arguments to argument parser
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)
