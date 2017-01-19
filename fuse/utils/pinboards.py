
class PinNotProcessed(Exception):
    pass

class Pinboard(object):

    def __init__(self):
        self.pins = []
        self.PinNotProcessed = PinNotProcessed

    def post(self, label, message):
        pin = Pin(label, message)
        self.pins.append(pin)

    def get(self, exclude):
        return [pin for i, pin in enumerate(self.pins) if i not in exclude]


class Pin(object):

    def __init__(self, label, message):
        self.label = label
        self.message = message
