
class PinNotProcessed(Exception):
    pass

class NoActionError(Exception):
    pass

class Pinboard(object):

    def __init__(self):
        self.pin_id = None
        self.pins = {}
        self.PinNotProcessed = PinNotProcessed

    def get_pin_id(self):
        if self.pin_id is None:
            self.pin_id = 1
            return self.pin_id

        self.pin_id += 1
        return self.pin_id



    def post(self, action, payload, sender=None, handler_filter=None, enforce=False):
        pin = Pin(action, payload, sender, handler_filter, enforce)
        pin_id = self.get_pin_id()

        self.pins[pin_id] = pin

        return pin_id

    def get(self, exclude):
        return [(pin_id, self.pins[pin_id]) for pin_id in self.pins if pin_id not in exclude]


class Pin(object):
    def __init__(self, action, payload, sender=None, handler_filter=None, enforce=False):
        self.action = action
        self.payload = payload
        self.sender = sender
        self.handler_filter = (lambda handler: True) if handler_filter is None else handler_filter
        self.enforce = enforce

    def is_recipient(self, handler):
        if not self.handler_filter(handler):
            return False

        if not hasattr(handler, self.action):
            if not self.enforce:
                return False
            else:
                raise NoActionError(
                    "Action `{action}` not found in handler `{handler}`".format(
                        action=self.action,
                        handler=handler)
                )

        return True

