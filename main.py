import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from main_window import STYLE, MainWindow


def resource_path(name: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    icon = resource_path("icon.ico")
    if os.path.exists(icon):
        app.setWindowIcon(QIcon(icon))
    window = MainWindow()
    window.resize(520, 760)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
