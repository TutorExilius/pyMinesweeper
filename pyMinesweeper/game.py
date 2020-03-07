from random import sample
from enum import IntEnum


class CellValue(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    MINE = 9


class Cell:
    def __init__(self, amount=CellValue.ZERO):
        self.amount = amount
        self.visible = False
        self.maybe_mine = False
    def __str__(self):
        return str(self.amount)

    def _get_mined(self):
        return self.amount == CellValue.MINE

    mined = property(_get_mined)


class Game:
    def __init__(self, parent, field_height, field_width, amount_mines):
        self.parent = parent
        self.field_height = field_height
        self.field_width = field_width
        self.amount_mines = amount_mines

        self.field = [[None] * field_width for _ in range(field_height)]
        self.initial_empty_field()

        self.left_free_nonmined_cells = field_height * field_width - amount_mines

    def won(self):
        print(self.left_free_nonmined_cells)
        return self.left_free_nonmined_cells == 0

    def initial_empty_field(self):
        for h in range(0, self.field_height):
            for w in range(0, self.field_width):
                self.field[h][w] = Cell()

    def mine_field(self, initial_clicked_pos):
        positions = [(h, w) for h in range(self.field_height) for w in range(self.field_width)]
        positions.remove(initial_clicked_pos)

        random_positions = sample(positions, self.amount_mines)

        for h, w in random_positions:
            self.field[h][w].amount = CellValue.MINE
            self.increment_neighboors((h, w))

    def update(self, pos):
        h, w = pos

        if self.field[h][w].amount != CellValue.MINE:
            current_cell = self.field[h][w].amount
            self.field[h][w].amount = CellValue(current_cell.value + 1)

    # returns amount of marked neighbors
    def on_neighbors(self, pos, callback):
        marked_neigbors = 0
        pos_h, pos_w = pos
        button = self.field[pos_h][pos_w].paired_button
        # left side
        if pos_w - 1 >= 0:
            if button.maybe_mine:
                marked_neigbors += 1

            callback((pos_h, pos_w - 1))

        # left top corner
        if pos_w - 1 >= 0 and pos_h - 1 >= 0:
            if button.maybe_mine:
                marked_neigbors += 1

            callback((pos_h - 1, pos_w - 1))

        # left bottom corner
        if pos_w - 1 >= 0 and pos_h + 1 < self.field_height:
            if button.maybe_mine:
                marked_neigbors += 1

            callback((pos_h + 1, pos_w - 1))

        # right side
        if pos_w + 1 < self.field_width:
            if button.maybe_mine:
                marked_neigbors += 1

            callback((pos_h, pos_w + 1))

        # right top corner
        if pos_w + 1 < self.field_width and pos_h - 1 >= 0:
            if button.maybe_mine:
                marked_neigbors += 1

            callback((pos_h - 1, pos_w + 1))

        # right bottom corner
        if pos_w + 1 < self.field_width and pos_h + 1 < self.field_height:
            if button.maybe_mine:
                marked_neigbors += 1

            callback((pos_h + 1, pos_w + 1))

        # top
        if pos_h - 1 >= 0:
            if button.maybe_mine:
                marked_neigbors += 1

            callback((pos_h - 1, pos_w))

        # bottom
        if pos_h + 1 < self.field_height:
            if button.maybe_mine:
                marked_neigbors += 1

            callback((pos_h + 1, pos_w))

        return marked_neigbors

    def increment_neighboors(self, pos):
        self.on_neighbors(pos, lambda pos: self.update(pos))

    def step_in_neighbors(self, pos):
        self.on_neighbors(pos, lambda pos: self.step_in(*pos))

    def start(self, initial_clicked_pos):
        self.mine_field(initial_clicked_pos)
        self.step_in(*initial_clicked_pos)

    def show_mines_and_game_over(self):
        for h in range(self.field_height):
            for w in range(self.field_width):
                if self.field[h][w].amount == CellValue.MINE:
                    self.field[h][w].visible = True
                    # self.field[h][w].paired_button.setStyleSheet("background-color: red")
                    self.field[h][w].paired_button.setText("💣")

    def step_in(self, h, w):
        if h not in range(self.field_height):
            return

        if w not in range(self.field_width):
            return

        if self.field[h][w].paired_button.maybe_mine or self.field[h][w].visible:
            return

        if self.field[h][w].visible:
            return

        if self.field[h][w].amount == CellValue.ZERO:
            self.field[h][w].visible = True
            self.left_free_nonmined_cells -= 1
            self.step_in(h - 1, w - 1)
            self.step_in(h - 1, w)
            self.step_in(h - 1, w + 1)
            self.step_in(h, w + 1)
            self.step_in(h + 1, w + 1)
            self.step_in(h + 1, w)
            self.step_in(h + 1, w - 1)
            self.step_in(h, w - 1)
        elif self.field[h][w].amount == CellValue.MINE:
            self.field[h][w].paired_button.setStyleSheet("background-color: red;")
            self.show_mines_and_game_over()
            self.parent.game_over()
        else:
            self.field[h][w].visible = True
            self.left_free_nonmined_cells -= 1
