import sys
from PyQt6.QtWidgets import QApplication
import qdarktheme

from ui import style


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarktheme.load_stylesheet())

    # 1.0 on small screens, up to 1.4 on large ones (1080p laptop at 100 % -> ~1.2).
    screen = app.primaryScreen().availableGeometry()
    style.configure_for_screen(screen.width(), screen.height())

    # Imported after the scale is set: widgets read it when they are built.
    from ui.main_window import MainWindow

    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
