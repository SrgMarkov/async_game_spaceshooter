import asyncio
import curses
import time
from itertools import cycle
from random import randint, choice

from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed


TIC_TIMEOUT = 0.1
STARS_SYMBOLS = ['+', '*', '.', ':']
STARS_COUNT = 100

COROUTINES = []


async def sleep(tics=1):
    """Sleep for tics."""
    for tic in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, offset_tics, symbol='*'):
    """
    Blink symbol on screen.
    """
    while offset_tics:
        offset_tics -= 1
        await asyncio.sleep(0)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)
        canvas.addstr(row, column, symbol)
        await sleep(3)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)
        canvas.addstr(row, column, symbol)
        await sleep(3)


async def fire(canvas, start_row, start_column,
               rows_speed=-0.3, columns_speed=0):
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
    """
    Animate spaceship, moving from left to right and from top to bottom.
    """
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
            row = max(0, row + row_move) if row_move < 0 else \
                min(row + row_move, max_row)
            column = max(0, column + column_move) if column_move < 0 else \
                min(column + column_move, max_column)
            draw_frame(canvas, row, column, frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, frame, negative=True)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom.
    Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    column = max(column, 0)
    column = min(column, columns_number - 1)
    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await sleep()
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


async def fill_orbit_with_garbage(canvas, max_column):
    """
    Fill orbit with garbage.
    """
    garbage_frames = []
    with open('animation/duck.txt', "r") as garbage_file:
        garbage_frames.append(garbage_file.read())
    with open('animation/hubble.txt', "r") as garbage_file:
        garbage_frames.append(garbage_file.read())
    with open('animation/lamp.txt', "r") as garbage_file:
        garbage_frames.append(garbage_file.read())
    with open('animation/trash_large.txt', "r") as garbage_file:
        garbage_frames.append(garbage_file.read())
    with open('animation/trash_small.txt', "r") as garbage_file:
        garbage_frames.append(garbage_file.read())
    with open('animation/trash_xl.txt', "r") as garbage_file:
        garbage_frames.append(garbage_file.read())
    global COROUTINES
    while True:
        garbage_frame = choice(garbage_frames)
        COROUTINES.append(fly_garbage(canvas, randint(0, max_column),
                                      garbage_frame))
        await sleep(10)


def draw(canvas):
    """"Draw animation."""
    canvas.nodelay(True)
    curses.curs_set(False)
    max_row, max_column = canvas.getmaxyx()
    fire_coroutine = fire(canvas, int(max_row - 1), int(max_column / 2))

    spaceship_start_row = int(max_row / 2)
    spaceship_start_column = int(max_column / 2)
    spaceship_coroutine = animate_spaceship(canvas, spaceship_start_row,
                                            spaceship_start_column, max_row,
                                            max_column)
    garbage_coroutine = fill_orbit_with_garbage(canvas, max_column)

    global COROUTINES
    COROUTINES = [fire_coroutine, spaceship_coroutine, garbage_coroutine]

    for star in range(STARS_COUNT):
        star_symbol = choice(STARS_SYMBOLS)
        star_append = randint(0, 20)
        coroutine = blink(canvas, randint(1, max_row - 1),
                          randint(1, max_column - 1), star_append, star_symbol)
        COROUTINES.append(coroutine)

    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
