class Message:
    def __init__(self, side, level, pattern):
        self.side=side
        self.level=level
        self.pattern=pattern

    def getSide(self):
        return self.side

    def getLevel(self):
        return self.level

    def getPattern(self):
        return self.pattern
