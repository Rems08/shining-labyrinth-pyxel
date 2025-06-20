from src.direction import Direction


class DirectionHelper:
    DIRS = {
        Direction.UP: (0, -1),
        Direction.DOWN: (0, 1),
        Direction.LEFT: (-1, 0),
        Direction.RIGHT: (1, 0),
    }

    @staticmethod
    def direction_to_value(direction: Direction) -> tuple[int, int]:
        if direction not in DirectionHelper.DIRS:
            raise ValueError(f"Invalid direction: {direction}")
        return DirectionHelper.DIRS[direction]
