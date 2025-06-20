class Screen:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    def __str__(self):
        return f"Screen(width={self.width}, height={self.height})"

    def __repr__(self):
        return self.__str__()
