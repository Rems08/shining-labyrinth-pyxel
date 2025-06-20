from player_movement_updater import PlayerMovementUpdater


class DannyPlayerMovementUpdater(PlayerMovementUpdater):

    def update(self, player):
        self.px += self.vx
        self.py += self.vy
        if self.px % CELL == 0 and self.py % CELL == 0:
            self.x, self.y = self.px // CELL, self.py // CELL
            self.moving = False

    def __init__(self):
        pass
