from __future__ import absolute_import, division, print_function, unicode_literals
import os

class Component(object):

    def __init__(self, name, logger):

        self.name = name
        self.logger = logger

        self.processed_pins = []
        self.context = {}
        self.files = {}

    def setup(self, pinboard, actions):
        sender = self
        handler_filter = lambda handler: handler is self

        for action in actions:
            payload = actions[action]
            pinboard.post(action, payload, sender, handler_filter, enforce=True)

    def configure(self, pinboard, prompt):
        """
        Process pins from pinboard and return number of pins processed
        """
        pins = pinboard.get(exclude=self.processed_pins)
        processed_pins = []
        deferred_pins = []

        for pin_id, pin in pins:
            if not pin.is_recipient(self):
                processed_pins.append(pin_id)
                continue

            try:
                getattr(self, pin.action)(payload=pin.payload, pinboard=pinboard, prompt=prompt)
                processed_pins.append(pin_id)
            except pinboard.PinNotProcessed:
                self.logger.info(
                    "Pin `{handler}/{action}` deferred".format(
                        handler=self,
                        action=pin.action,
                    )
                )
                deferred_pins.append(pin_id)

        self.processed_pins += processed_pins

        result = len(processed_pins) + len(deferred_pins)

        return result

    def write(self):
        for target in self.files:

            try:
                os.makedirs(os.path.dirname(target))
            except OSError:
                pass

            with open(target, 'w') as fp:
                fp.write(self.files[target])

    def finalize(self):
        pass

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


