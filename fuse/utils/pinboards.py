
class PinNotProcessed(Exception):
    pass

class NoActionError(Exception):
    pass

class Pinboard(object):

    def __init__(self):
        self.pin_id = None
        self.pins = []
        self.PinNotProcessed = PinNotProcessed
        self.next_index = 0

    def get_pin_id(self):
        if self.pin_id is None:
            self.pin_id = 1
            return self.pin_id

        self.pin_id += 1
        return self.pin_id



    def post(self, action, payload, sender=None, handler_filter=None,
            enforce=False, upnext=False):

        pin = Pin(action, payload, sender, handler_filter, enforce)
        pin_id = self.get_pin_id()

        if upnext:
            self.pins.insert(self.next_index, (pin_id, pin))
        else:
            self.pins.append((pin_id, pin))

        return pin_id

    def get(self, exclude):
        try:
            pin_id, pin = self.pins[self.next_index]
        except IndexError:
            self.next_index = 0
            raise StopIteration

        self.next_index += 1

        if pin_id in exclude:
            return self.get(exclude)
        else:
            return pin_id, pin

    def __len__(self):
        return len(self.pins)


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

