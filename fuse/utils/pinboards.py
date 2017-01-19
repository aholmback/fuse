
class Pinboard(object):

    def __init__(self):
        self.pins = []

    def post(self, label, message):
        pin = Pin(label, message)
        self.pins.append(pin)

    def repost(self, index):
        self.pins.append(self.pins.pop(index))

    def get(self, from_index):
        return self.pins[from_index:]


class Pin(object):

    def __init__(self, label, message):
        self.label = label
        self.message = message
