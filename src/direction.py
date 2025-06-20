from enum import Enum


class Direction(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, direction_str: str):
        try:
            return cls[direction_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid direction: {direction_str}")
