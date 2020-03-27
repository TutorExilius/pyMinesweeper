import sys

from PyQt5.QtWidgets import QApplication
from pyMinesweeper.main_window import MainWindow


def main():
    app = QApplication([])

    height = 8
    width = 8
    amount_mines = 10
    main_window = MainWindow(height, width, amount_mines)
    main_window.show()

    sys.exit(app.exec_() or 0)


if __name__ == "__main__":
    main()
