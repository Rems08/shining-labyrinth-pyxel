from direction import Direction


class OrientationMapper:
    def __init__(self, cell_size):
        self.orientation_map = {
            Direction.UP: 0,
            Direction.DOWN: cell_size,
            Direction.LEFT: cell_size * 2,
            Direction.RIGHT: cell_size * 3,
        }

    def map_orientation(self, value):
        orientation = self.orientation_map.get(value, None)
        if orientation is None:
            raise ValueError(f"Invalid direction: {value}")
        return orientation
