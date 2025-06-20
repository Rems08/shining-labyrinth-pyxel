from abc import ABC, abstractmethod


class PlayerMovementDrawer(ABC):

    @abstractmethod
    def draw(self, player, position):
        pass
