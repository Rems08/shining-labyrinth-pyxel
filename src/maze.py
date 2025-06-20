from typing import List


class Maze:
    def __init__(self,
                 width: int,
                 height: int,
                 grid: List[List[int]]) -> None:
        self.width = width
        self.height = height
        self.grid = grid

    """
    Check wether a position is within the bounds of the maze.
    """

    def is_within_bounds(self, x: int, y: int) -> bool:
        return self.grid[y][x] == 1
        return 0 <= x < len(self.grid) and 0 <= y < len(self.grid[0])
