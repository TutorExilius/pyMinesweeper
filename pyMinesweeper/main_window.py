import enum
import functools
import webbrowser
import PyQt5
from PyQt5.QtCore import QEvent, QTimer, QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QSound
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QPushButton
from PyQt5 import uic, QtGui
from pathlib import Path

from pyMinesweeper.game import Game


class GameMode(enum.IntEnum):
    BEGINNER = 0
    INTERMEDIATE = 1
    EXPERT = 2


class MainWindow(QMainWindow):
    def __init__(self, height, width, amount_mines, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi(Path(__file__).parent / "ui" / "main_window.ui", self)

        # Sounds
        self.sound_beginner_mode = str(
            Path(__file__).parent / "sounds" / "beginner_mode.wav"
        )
        self.sound_intermediate_mode = str(
            Path(__file__).parent / "sounds" / "intermediate_mode.wav"
        )
        self.sound_expert_mode = str(
            Path(__file__).parent / "sounds" / "expert_mode.wav"
        )
        self.sound_beginner_win = str(
            Path(__file__).parent / "sounds" / "beginner_win.wav"
        )
        self.sound_intermediate_win = str(
            Path(__file__).parent / "sounds" / "intermediate_win.wav"
        )
        self.sound_expert_win = str(Path(__file__).parent / "sounds" / "expert_win.wav")
        self.sound_flag = str(Path(__file__).parent / "sounds" / "flag.wav")
        self.sound_no_flag = str(Path(__file__).parent / "sounds" / "no_flag.wav")
        self.sound_reset = str(Path(__file__).parent / "sounds" / "reset_game.wav")
        self.sound_click = str(Path(__file__).parent / "sounds" / "click.wav")
        self.sound_boom = str(Path(__file__).parent / "sounds" / "boom.wav")
        self.sound_bye = str(Path(__file__).parent / "sounds" / "bye.wav")
        self.sound_donate = str(Path(__file__).parent / "sounds" / "donate.wav")

        # Qt: connect reset button
        self.pushButton_reset.clicked.connect(self.on_reset_clicked)
        self.pushButton_beginner.clicked.connect(self.change_to_beginner_mode)
        self.pushButton_intermediate.clicked.connect(self.change_to_intermediate_mode)
        self.pushButton_expert.clicked.connect(self.change_to_expert_mode)
        self.actionSupport_Tutor_Exilius.triggered.connect(self.open_twitch_support_page)
        self.action_About_Qt.triggered.connect(self.on_about_qt)

        self.height = height
        self.width = width
        self.amount_mines = amount_mines
        self.minesweeper = None
        self.current_mode = GameMode.BEGINNER

        # Media Player - to play bye.wav synchronously
        self.player = QMediaPlayer()
        self.player.setVolume(100)

        # Timer
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

    def playsound(self, sound_file):
        try:
            print("Play sound:", sound_file)

            if sound_file == self.sound_bye:
                self.player.setMedia(QMediaContent(QUrl.fromLocalFile(sound_file)))
                self.player.play()
            else:
                QSound.play(sound_file)

        except Exception as e:
            print("Played too fast?")
            print(e)

    def closeEvent(self, event):
        # small hack :)
        # DO FIRST: link next close event to self.force_closeEvent(..)
        self.closeEvent = self.force_closeEvent

        # end of playing 'self.sound_bye' will occure next close()
        # --> self.force_closeEvent(..) will be called
        self.player.stateChanged.connect(self.on_bye_played)

        self.playsound(self.sound_bye)

        event.ignore()

    def force_closeEvent(self, event):
        event.accept()

    def on_bye_played(self, state):
        if state == QMediaPlayer.StoppedState:
            self.close()

    def on_reset_clicked(self):
        self.reset()
        self.playsound(self.sound_reset)

    def on_about_qt(self):
        QMessageBox.aboutQt(self)

    def change_to_beginner_mode(self):
        self.current_mode = GameMode.BEGINNER
        self.height = 8
        self.width = 8
        self.amount_mines = 10
        self.reset()
        self.playsound(self.sound_beginner_mode)

    def change_to_intermediate_mode(self):
        self.current_mode = GameMode.INTERMEDIATE
        self.height = 16
        self.width = 16
        self.amount_mines = 40
        self.reset()
        self.playsound(self.sound_intermediate_mode)

    def change_to_expert_mode(self):
        self.current_mode = GameMode.EXPERT
        self.height = 16
        self.width = 32
        self.amount_mines = 99
        self.reset()
        self.playsound(self.sound_expert_mode)

    def start_game_timer(self):
        self.timer.start(1000)

    def stop_game_timer(self):
        self.timer.stop()

    def update_lcd_timer(self):
        value = self.lcdNumber_playing_time.intValue()
        self.lcdNumber_playing_time.display(value + 1)

    def initialise_field(self):
        self.clear_layout(self.gridLayout)
        button_size = (40, 40)
        font = QFont()
        font.setPointSize(15)
        font.setBold(False)

        if self.current_mode == GameMode.INTERMEDIATE:
            font.setPointSize(11)
            button_size = (32, 32)
        elif self.current_mode == GameMode.EXPERT:
            font.setPointSize(11)
            button_size = (32, 32)

        for h in range(self.height):
            for w in range(self.width):
                button = QPushButton()
                button.setFixedSize(button_size[0], button_size[1])
                button.setFont(font)
                button.meta = (h, w)
                button.mouseReleaseEvent = functools.partial(
                    self.on_mouse_release_event, button
                )
                button.mousePressEvent = functools.partial(
                    self.on_mouse_press_event, button
                )
                button.maybe_mine = False
                button.pressed = False
                button.paired_cell = self.minesweeper.field[h][w]
                self.gridLayout.addWidget(button, h, w)
                self.minesweeper.field[h][w].paired_button = button

        # resizing this way doesn't work.
        self.setFixedSize(self.sizeHint())
        QTimer.singleShot(0, lambda: self.setFixedSize(self.sizeHint()))
        # see: https://forum.qt.io/topic/4500/resize-top-level-window-to-fit-contents/4

    def on_mouse_press_event(self, button, ev):
        cell_visible = button.paired_cell.visible
        if not cell_visible and not button.maybe_mine and not button.pressed:
            # and ev.button() == PyQt5.QtCore.Qt.LeftButton:
            button.pressed = True
            button.setStyleSheet("border: 3px inset #aaa;")

    def on_mouse_release_event(self, button, ev):
        h, w = button.meta
        cell_visible = button.paired_cell.visible
        expected_amount_mines_in_area = button.paired_cell.amount.value

        if ev.button() == PyQt5.QtCore.Qt.LeftButton:
            if not cell_visible and not button.maybe_mine and button.pressed:
                button.pressed = False
                button.setStyleSheet("border: 0px")

                self.playsound(self.sound_click)

            if cell_visible and self.all_mines_in_area_marked(
                    expected_amount_mines_in_area, (h, w)
            ):
                # todo: implement step_in_all_fields_area()

                self.step_in_neighbors((h, w))
            elif not button.maybe_mine:
                self.step_in(*button.meta)
        elif ev.button() == PyQt5.QtCore.Qt.RightButton:
            # ignore visible fields
            if not button.paired_cell.visible:
                if button.maybe_mine:
                    self.playsound(self.sound_no_flag)

                    button.setStyleSheet("")
                    button.setText("")
                    self.increment_mines_lcd()
                    button.maybe_mine = not button.maybe_mine
                else:
                    if self.decrement_mines_lcd():
                        self.playsound(self.sound_flag)

                        button.setStyleSheet(
                            "border: 1px solid black; background-color: #efefef;"
                        )
                        button.setText("🚩")
                        button.maybe_mine = not button.maybe_mine
                    else:
                        button.setStyleSheet("")
        ev.accept()

    def all_mines_in_area_marked(self, expected_amount_mines_in_area, pos):
        mines_in_area = self.minesweeper.on_neighbors(pos, lambda pos: None)
        print("marked:", mines_in_area)
        return mines_in_area == expected_amount_mines_in_area

    def step_in_neighbors(self, pos):
        # pass  # not implemented yet
        self.minesweeper.step_in_neighbors(pos)

    def increment_mines_lcd(self):
        value = self.lcdNumber_amount_mines.intValue()
        self.lcdNumber_amount_mines.display(value + 1)

    def decrement_mines_lcd(self):
        value = self.lcdNumber_amount_mines.intValue()

        if value > 0:
            self.lcdNumber_amount_mines.display(value - 1)
            return True
        else:
            return False

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
        try:
            if not self.initial_clicked:
                self.start((h, w))
                self.initial_clicked = True
            else:
                self.minesweeper.step_in(h, w)

            self.update_ui()
        except Exception as e:
            print(e)

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
                        field[h][w].paired_button.setStyleSheet(
                            "border: 1px solid #333"
                        )

                        # field[h][w].paired_button.setVisible(False)
                    else:
                        field[h][w].paired_button.setStyleSheet(
                            "border: 1px solid #333"
                        )

                    field[h][w].paired_button.setText(text)

        if self.minesweeper.won():
            if self.current_mode == GameMode.BEGINNER:
                self.playsound(self.sound_beginner_win)
            elif self.current_mode == GameMode.INTERMEDIATE:
                self.playsound(self.sound_intermediate_win)
            else:
                self.playsound(self.sound_expert_win)

            self.pushButton_reset.setText("😁")
            self.stop_game_timer()
            # self.show_message_box("Finished", "You WON!")
            self.disable_field()

    def game_over(self):
        self.playsound(self.sound_boom)
        self.pushButton_reset.setText("😵")
        self.stop_game_timer()
        # self.show_message_box("Finished", "GAME OVER :(")
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

    def open_twitch_support_page(self):
        self.playsound(self.sound_donate)
        webbrowser.open("https://streamlabs.com/tutorexilius")
