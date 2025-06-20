from direction import Direction
from player_movement_drawer import PlayerMovementDrawer
from position import Position


class Player:
    def __init__(self,
                 name: str,
                 position: Position,
                 pixel_position: Position,
                 orientation: Direction,
                 drawer: PlayerMovementDrawer):
        self.name = name
        self.position = position
        self.pixel_position = pixel_position
        self.orientation = orientation
        self.drawer = drawer

    def __str__(self):
        return f"Player(name={self.name}, position={self.position})"

    def is_colliding(self, other: 'Player') -> bool:
        if not isinstance(other, Player):
            return NotImplemented
        return self.position == other.position

    def move(self):
        pass

    def draw(self):
        self.drawer.draw(self, self.position)
