import asyncio
import curses
import os
import time
from itertools import cycle
from random import randint, choice

from curses_tools import draw_frame, read_controls, get_frame_size
from explosion import explode
from game_scenario import get_garbage_delay_tics, PHRASES
from obstacles import Obstacle
from physics import update_speed


TIC_TIMEOUT = 0.1
STARS_SYMBOLS = ['+', '*', '.', ':']
STARS_COUNT = 100
GUN_GET_YEAR = 2020

coroutines = []
obstacles = []
obstacles_in_last_collisions = []
year = 1957


async def sleep(tics=1):
    """Sleep for tics."""
    for tic in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, offset_tics, symbol='*'):
    """
    Blink star symbol on screen.
    """
    await sleep(offset_tics)
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
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                return obstacles_in_last_collisions.append(obstacle)
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

    center_row, center_column = max_row // 2, max_column // 2
    ship_size_row, ship_size_column = get_frame_size(frame_1)
    max_row -= ship_size_row
    max_column -= ship_size_column
    frames = [frame_1, frame_2]
    row_speed = column_speed = 0

    for frame in cycle(frames):
        for game_cycle in range(2):
            row_move, column_move, space_press = read_controls(canvas)
            row = max(0, row + row_move) if row_move < 0 else min(row + row_move, max_row)
            column = max(0, column + column_move) if column_move < 0 else min(column + column_move, max_column)
            row_speed, column_speed = update_speed(row_speed, column_speed, row_move, column_move)
            row, column = row + row_speed, column + column_speed

            if space_press and year >= GUN_GET_YEAR:
                shoot = fire(canvas, row, column + ship_size_column / 2, rows_speed=-5)
                coroutines.append(shoot)

            draw_frame(canvas, row, column, frame)
            await sleep()
            draw_frame(canvas, row, column, frame, negative=True)

        for obstacle in obstacles:
            if obstacle.has_collision(row, column, ship_size_row, ship_size_column):
                await explode(canvas, row, column)
                await show_gameover(canvas, center_row, center_column)
                return obstacles_in_last_collisions.remove(obstacle)



async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom.
    Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    column = max(column, 0)
    column = min(column, columns_number - 1)
    row = 0

    while row < rows_number:
        garbage_size_row, garbage_size_column = get_frame_size(garbage_frame)
        draw_frame(canvas, row, column, garbage_frame)
        obstacle = Obstacle(row, column, garbage_size_row, garbage_size_column)
        obstacles.append(obstacle)
        await sleep()
        obstacles.pop(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        if obstacle in obstacles_in_last_collisions:
            await explode(canvas, row, column)
            return obstacles_in_last_collisions.remove(obstacle)
        row += speed


async def fill_orbit_with_garbage(canvas, max_column):
    """
    Fill orbit with garbage.
    """
    garbage_frames = []
    trash_frames = os.listdir('animation/trash_frames')
    for trash_frame in trash_frames:
        with open(f'animation/trash_frames/{trash_frame}', 'r') as garbage_file:
            garbage_frames.append(garbage_file.read())
    while True:
        garbage_delay_tics = get_garbage_delay_tics(year)
        if garbage_delay_tics:
            garbage_frame = choice(garbage_frames)
            coroutines.append(fly_garbage(canvas, randint(0, max_column),
                                          garbage_frame))
            await sleep(garbage_delay_tics)
        else:
            await sleep()


async def show_gameover(canvas, center_row, center_column):
    """Show game over screen."""
    with open('animation/game_over.txt', 'r') as game_over:
        game_over_frame = game_over.read()
    frame_rows, frame_columns = get_frame_size(game_over_frame)
    while True:
        draw_frame(canvas, center_row - frame_rows / 2, center_column - frame_columns / 2, game_over_frame)
        await sleep()


async def show_year(canvas, max_row):
    """Show year and information."""
    global year
    while True:
        information_line = '                                              '
        if year in PHRASES:
            information_line = f' - {PHRASES[year]}'
        text_line = canvas.derwin(max_row - 2, 2)
        text_line.addstr(f'Year: {year}{information_line}')
        year += 1
        await sleep(15)


def draw(canvas):
    """"Draw animation."""
    canvas.nodelay(True)
    curses.curs_set(False)
    max_row, max_column = canvas.getmaxyx()

    global coroutines
    coroutines = [
        fire(canvas, int(max_row - 1), int(max_column / 2)),
        animate_spaceship(canvas, int(max_row / 2), int(max_column / 2), max_row, max_column),
        fill_orbit_with_garbage(canvas, max_column),
        show_year(canvas, max_row)]

    for star in range(STARS_COUNT):
        star_symbol = choice(STARS_SYMBOLS)
        star_append = randint(0, 20)
        coroutine = blink(canvas, randint(1, max_row - 1),
                          randint(1, max_column - 1), star_append, star_symbol)
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
