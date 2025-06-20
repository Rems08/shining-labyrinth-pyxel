import pyxel

from direction import Direction
from orientation_mapper import OrientationMapper
from player import Player
from player_movement_drawer import PlayerMovementDrawer
from screen import Screen
from src.position import Position


class DefaultPlayerMovementDrawer(PlayerMovementDrawer):
    def __init__(self,
                 orientation_mapper: OrientationMapper,
                 cell_size: int,
                 screen: Screen,
                 image_bank: int):
        super().__init__()
        self.orientation_mapper = orientation_mapper
        self.cell_size = cell_size
        self.screen = screen
        self.image_bank = image_bank

    def draw(self, player: Player, camera_position: Position):
        dx = player.pixel_position.x - camera_position.x
        dy = player.pixel_position.y - camera_position.y

        if not (-self.cell_size < dx < self.screen.width and -self.cell_size < dy < self.screen.height):
            return

        u = self.orientation_mapper.map_orientation(player.orientation)
        if player.orientation == Direction.LEFT:
            pyxel.blt(dx, dy, self.image_bank, u, 0, -self.cell_size, self.cell_size, 0)
        else:
            pyxel.blt(dx, dy, self.image_bank, u, 0, self.cell_size, self.cell_size, 0)
