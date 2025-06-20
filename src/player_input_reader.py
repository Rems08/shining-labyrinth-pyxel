import pyxel

from src.maze import Maze


class PlayerInputReader:
    def __init__(self, maze: Maze, player_input):
        self.maze = maze
        self.player_input = player_input

    def read(self):
        keymap = {
            pyxel.KEY_LEFT: "LEFT",
            pyxel.KEY_RIGHT: "RIGHT",
            pyxel.KEY_UP: "UP",
            pyxel.KEY_DOWN: "DOWN",
        }
        for key, d in keymap.items():
            if pyxel.btnp(key):
                dx, dy = DIRS[d]
                nx, ny = self.x + dx, self.y + dy
                if (0 <= nx < self.maze.width
                        and 0 <= ny < self.maze.height
                        and self.maze.is_within_bounds(nx, ny)):
                    self.dir = d
                    self.moving = True
                    self.vx, self.vy = dx * PLAYER_SPEED, dy * PLAYER_SPEED
                break
