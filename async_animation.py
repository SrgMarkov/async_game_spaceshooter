import asyncio
import curses
import time
from itertools import cycle
from random import randint, choice
from curses_tools import draw_frame, read_controls, get_frame_size


TIC_TIMEOUT = 0.1
STARS_SYMBOLS = ['+', '*', '.', ':']
STARS_COUNT = 100


async def blink(canvas, row, column, offset_tics, symbol='*'):
    while offset_tics:
        offset_tics -= 1
        await asyncio.sleep(0)
    while True:
        for tic in range(20):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)

        for tic in range(3):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)

        for tic in range(5):
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await asyncio.sleep(0)

        for tic in range(3):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, row, column, max_row, max_column):
    with open('animation/rocket_frame_1.txt', 'r') as rocket_frame_1:
        frame_1 = rocket_frame_1.read()
    with open('animation/rocket_frame_2.txt', 'r') as rocket_frame_2:
        frame_2 = rocket_frame_2.read()

    ship_size_row, ship_size_column = get_frame_size(frame_1)
    max_row -= ship_size_row
    max_column -= ship_size_column
    frames = [frame_1, frame_2]

    for frame in cycle(frames):
        for game_cycle in range(2):
            row_move, column_move, space_press = read_controls(canvas)
            row = max(0, row + row_move) if row_move < 0 else min(row + row_move, max_row)
            column = max(0, column + column_move) if column_move < 0 else min(column + column_move, max_column)
            draw_frame(canvas, row, column, frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, frame, negative=True)


def draw(canvas):
    canvas.nodelay(True)
    curses.curs_set(False)
    max_row, max_column = canvas.getmaxyx()
    fire_coroutine = fire(canvas, int(max_row - 1), int(max_column / 2))

    spaceship_start_row = int(max_row / 2)
    spaceship_start_column = int(max_column / 2)
    spaceship_coroutine = animate_spaceship(canvas, spaceship_start_row, spaceship_start_column, max_row, max_column)

    coroutines = [fire_coroutine, spaceship_coroutine]

    for star in range(STARS_COUNT):
        star_symbol = choice(STARS_SYMBOLS)
        star_append = randint(0, 20)
        coroutine = blink(canvas, randint(1, max_row - 1), randint(1, max_column - 1), star_append, star_symbol)
        coroutines.append(coroutine)

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
