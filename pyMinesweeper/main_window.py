import functools
import PyQt5
from PyQt5.QtCore import QEvent, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from PyQt5 import uic, Qt, QtGui, QtCore
from pathlib import Path
from minesweeper.game import Game


class MainWindow(QMainWindow):
    def __init__(self, height, width, amount_mines, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi(Path(__file__).parent / "ui" / "main_window.ui", self)

        # QT: connect reset button
        self.pushButton_reset.clicked.connect(self.reset)
        self.pushButton_beginner.clicked.connect(self.change_to_beginner_mode)
        self.pushButton_intermediate.clicked.connect(self.change_to_intermediate_mode)
        self.pushButton_expert.clicked.connect(self.change_to_expert_mode)

        self.action_About_Qt.triggered.connect(self.on_about_qt)

        self.height = height
        self.width = width
        self.amount_mines = amount_mines
        self.minesweeper = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_lcd_timer)

        self.initial_clicked = False

        palette = self.lcdNumber_amount_mines.palette()
        palette.setColor(palette.WindowText, QtGui.QColor(255, 0, 0))
        palette.setColor(palette.Light, QtGui.QColor(255, 0, 0))
        palette.setColor(palette.Dark, QtGui.QColor(255, 0, 0))

        self.lcdNumber_amount_mines.setPalette(palette)
        self.lcdNumber_playing_time.setPalette(palette)

        self.reset()

    def on_about_qt(self):
        QMessageBox.aboutQt(self)

    def change_to_beginner_mode(self):
        self.height = 8
        self.width = 8
        self.amount_mines = 10
        self.reset()

    def change_to_intermediate_mode(self):
        self.height = 16
        self.width = 16
        self.amount_mines = 40
        self.reset()

    def change_to_expert_mode(self):
        self.height = 16
        self.width = 32
        self.amount_mines = 99
        self.reset()

    def start_game_timer(self):
        self.timer.start(1000)

    def stop_game_timer(self):
        self.timer.stop()

    def update_lcd_timer(self):
        value = self.lcdNumber_playing_time.intValue()
        self.lcdNumber_playing_time.display(value + 1)

    def initialise_field(self):
        self.clear_layout(self.gridLayout)

        for h in range(self.height):
            for w in range(self.width):
                button = QPushButton()
                button.setFixedSize(45, 45)
                font = QFont()
                font.setBold(False)
                font.setPointSize(14)
                button.setFont(font)
                button.meta = (h, w)
                button.mousePressEvent = functools.partial(
                    self.my_mouse_press_event, button)
                button.maybe_mine = False
                button.paired_cell = self.minesweeper.field[h][w]
                self.gridLayout.addWidget(button, h, w)
                self.minesweeper.field[h][w].paired_button = button

        # resizing this way doesn't work.
        self.setFixedSize(self.sizeHint())
        QTimer.singleShot(0, lambda: self.setFixedSize(self.sizeHint()))
        # see: https://forum.qt.io/topic/4500/resize-top-level-window-to-fit-contents/4

    def my_mouse_press_event(self, button, ev):
        h, w = button.meta
        cell_visible = button.paired_cell.visible
        expected_amount_mines_in_area = button.paired_cell.amount.value

        if ev.button() == PyQt5.QtCore.Qt.LeftButton:
            if cell_visible and self.all_mines_in_area_marked(
                    expected_amount_mines_in_area, (h, w)):
                # todo: implement step_in_all_fields_area()

                self.step_in_neighbors((h, w))
            elif not button.maybe_mine:
                self.step_in(*button.meta)
        elif ev.button() == PyQt5.QtCore.Qt.RightButton:
            # ignore visible fields
            if not button.paired_cell.visible:
                if button.maybe_mine:
                    button.setStyleSheet("")
                    self.increment_mines_lcd()
                    button.maybe_mine = not button.maybe_mine
                else:
                    if self.decrement_mines_lcd():
                        button.setStyleSheet("background-color: #FFC3C3;")
                        button.maybe_mine = not button.maybe_mine
        ev.accept()

    def all_mines_in_area_marked(self, expected_amount_mines_in_area, pos):
        mines_in_area = self.minesweeper.on_neighbors(pos, lambda pos: None)
        return mines_in_area == expected_amount_mines_in_area

    def step_in_neighbors(self, pos):
        self.minesweeper.step_in_neighbors(pos)

    def increment_mines_lcd(self):
        value = self.lcdNumber_amount_mines.intValue()
        self.lcdNumber_amount_mines.display(value + 1)

    def decrement_mines_lcd(self):
        value = self.lcdNumber_amount_mines.intValue()

        if value > 0:
            self.lcdNumber_amount_mines.display(value - 1)
            return True

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def start(self, initial_click_pos):
        self.start_game_timer()
        self.minesweeper.start(initial_click_pos)

    def reset(self):
        self.minesweeper = Game(self, self.height, self.width, self.amount_mines)
        self.lcdNumber_amount_mines.display(self.amount_mines)
        self.initial_clicked = False
        self.initialise_field()
        self.enable_field()
        self.stop_game_timer()
        self.lcdNumber_playing_time.display(0)
        self.pushButton_reset.setText("😊")

    def step_in(self, h, w):
        if not self.initial_clicked:
            self.start((h, w))
            self.initial_clicked = True
        else:
            self.minesweeper.step_in(h, w)

        self.update_ui()

    def update_ui(self):
        field = self.minesweeper.field

        for h in range(self.minesweeper.field_height):
            for w in range(self.minesweeper.field_width):
                if field[h][w].visible:
                    text = str(field[h][w].amount.value)

                    if text == "9":
                        text = "💣"
                    elif text == "0":
                        text = ""
                        field[h][w].paired_button.setStyleSheet("border: 1px solid #333")

                        # field[h][w].paired_button.setVisible(False)
                    else:
                        field[h][w].paired_button.setStyleSheet("border: 1px solid #333")

                    field[h][w].paired_button.setText(text)

        if self.minesweeper.won():
            self.pushButton_reset.setText("😁")

            self.stop_game_timer()

            self.show_message_box("Finished", "You WON!")
            self.disable_field()

    def game_over(self):
        self.pushButton_reset.setText("😵")

        self.stop_game_timer()

        self.show_message_box("Finished", "GAME OVER :(")
        self.disable_field()

    def disable_field(self):
        for h in range(self.minesweeper.field_height):
            for w in range(self.minesweeper.field_width):
                self.minesweeper.field[h][w].paired_button.setEnabled(False)

    def enable_field(self):
        for h in range(self.minesweeper.field_height):
            for w in range(self.minesweeper.field_width):
                self.minesweeper.field[h][w].paired_button.setEnabled(True)

    def show_message_box(self, title, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.exec_()
