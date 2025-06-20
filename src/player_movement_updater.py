from abc import ABC, abstractmethod


class PlayerMovementUpdater(ABC):

    @abstractmethod
    def update(self, player):
        pass
