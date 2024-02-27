import sys

from PyQt6.QtWidgets import QApplication
from main import MainWindow

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())
