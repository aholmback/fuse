from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.utils.decorators import static_vars
import fuse

@static_vars(pinboards={})
def get_pinboard(identifier):
    # (Instantiate) and return Pinboard: One object per name.
    if identifier not in get_pinboard.pinboards:
        get_pinboard.pinboards[identifier] = Pinboard()

    return get_pinboard.pinboards[identifier]

class NoActionError(Exception):
    pass

class PinNotProcessed(Exception):
    pass

class Pinboard(object):

    FIRST = 0
    UPNEXT = 1
    LAST = -1

    def __init__(self):
        self.pin_id = None
        self.pins = []
        self.NoActionError = NoActionError
        self.next_index = 0
        self.visitors = []
        self.PinNotProcessed = PinNotProcessed

    def get_pin_id(self):
        if self.pin_id is None:
            self.pin_id = 1
            return self.pin_id

        self.pin_id += 1
        return self.pin_id

    def post(self, action, payload, sender=None, visitor_filter=None,
            enforce=False, position=None):

        # Set default position constant (should always be LAST)
        if position is None:
            position = self.LAST

        # Translate position constant to corresponding index
        index = {
            self.FIRST: 0,
            self.UPNEXT: self.next_index,
            self.LAST: len(self.pins),
        }[position]

        if index < self.next_index:
            self.next_index += 1

        pin_id = self.get_pin_id()

        # Create pin and generate pin_id
        pin = Pin(pin_id, action, payload, sender, visitor_filter, enforce)


        # Insert pin+pin_id at given index
        self.pins.insert(index, (pin_id, pin))

        fuse.log.info("posting pin {pin} at {index} (next/last: {next_index}/{last}) (enforce={enforce})".format(
            index=index,
            next_index=self.next_index,
            pin=pin,
            enforce=enforce,
            last=len(self.pins)-1,
        ))

        return pin_id

    def get_next(self, exclude):
        try:
            pin_id, pin = self.pins[self.next_index]
        except IndexError:
            self.next_index = 0
            raise StopIteration

        self.next_index += 1

        if pin_id in exclude:
            return self.get_next(exclude)
        else:
            return pin_id, pin

class Pin(object):
    def __init__(self, identifier, action, payload, sender=None, visitor_filter=None, enforce=False):
        self.identifier = identifier
        self.action = action
        self.payload = payload
        self.sender = sender
        self.visitor_filter = (lambda visitor: True) if visitor_filter is None else visitor_filter
        self.enforce = enforce

    def __str__(self):
        return "{action} ({identifier})".format(action=self.action, identifier=self.identifier)

    def __unicode__(self):
        return "{action} ({identifier})".format(action=self.action, identifier=self.identifier)

