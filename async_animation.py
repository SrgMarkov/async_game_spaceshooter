import asyncio
import curses
import time
from random import randint, choice
from curses_tools import draw_frame, read_controls, get_frame_size


TIC_TIMEOUT = 0.1
STARS_SYMBOLS = ['+', '*', '.', ':']
STARS_COUNT = 300


async def blink(canvas, row, column, symbol='*'):
    while True:
        for tic in range(randint(1, 20)):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)

        for tic in range(randint(1, 3)):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)

        for tic in range(randint(1, 5)):
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await asyncio.sleep(0)

        for tic in range(randint(1, 3)):
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


def get_moving(route, move, ship_size, max_coord):
    if 0 <= route + move <= max_coord - ship_size:
        return route + move
    elif route + move < 0:
        return 0
    elif route + move > max_coord:
        return max_coord - ship_size


async def animate_spaceship(canvas, row, column, max_coords):
    with open('animation/rocket_frame_1.txt', 'r') as rocket_frame_1:
        frames = [rocket_frame_1.read()]
    with open('animation/rocket_frame_2.txt', 'r') as rocket_frame_2:
        frames.append(rocket_frame_2.read())

    max_row, max_column = max_coords[0], max_coords[1]
    ship_size_row, ship_size_column = get_frame_size(frames[0])

    while True:
        row_move, column_move, space_press = read_controls(canvas)

        draw_frame(canvas, row, column, frames[1], negative=True)
        row = get_moving(row, row_move, ship_size_row, max_row)
        column = get_moving(column, column_move, ship_size_column, max_column)
        draw_frame(canvas, row, column, frames[0])
        await asyncio.sleep(0)

        draw_frame(canvas, row, column, frames[0], negative=True)
        draw_frame(canvas, row, column, frames[1])
        await asyncio.sleep(0)


def draw(canvas):
    canvas.nodelay(True)
    curses.curs_set(False)
    max_coords = canvas.getmaxyx()
    max_row, max_column = max_coords[0] - 1, max_coords[1] - 1
    fire_coroutine = fire(canvas, int(max_row), int(max_column / 2))
    coroutines = [fire_coroutine]

    spaceship_start_row = int(max_row / 2)
    spaceship_start_column = int(max_column / 2)
    spaceship_coroutine = animate_spaceship(canvas, spaceship_start_row, spaceship_start_column, max_coords)

    for star in range(STARS_COUNT):
        star_symbol = choice(STARS_SYMBOLS)
        coroutine = blink(canvas, randint(1, max_row), randint(1, max_column), star_symbol)
        coroutines.append(coroutine)

    while True:
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        spaceship_coroutine.send(None)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
