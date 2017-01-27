from __future__ import absolute_import, division, print_function, unicode_literals
import os
import importlib
import json
import collections
from cement.core.exc import CaughtSignal
from fuse.utils import files, pinboards
import fuse

class Lineup(object):
    """
    Read configuration
    Invoke component functions
    Write to disk
    """

    def __init__(self, configuration):
        # Parse configuration
        # Accept filename (without extension) as source
        # TODO: Implement http and local path

        self.components = []

        configuration_source = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'lineups',
            '%s.json' % configuration,
        )

        with open(configuration_source) as f:
            self.configuration = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(f.read())

    def fuse(self):
        """
        Single point entry.

        Takes: Some json lineup
        Gives: A configured set of components
        """
        self.read()
        self.invoke()
        self.write()

    def read(self):
        self.load_pinboard()
        self.load_components()

    def load_pinboard(self):
        # Post all actions in configuration to pinboard
        # Don't load the components
        pinboard = pinboards.get_pinboard('components')
        
        for component_name, actions in self.configuration.items():
            for action, payload in actions.items():
                # When an action is queued more than once an identifier must exist
                # the prevent the action identifiers from clashing.
                # This will, by procedure, correspond to the index of the context
                # stash that the action will write to.
                # Nothing will be done to enforce the index of the context stash
                # to be the same as the action suggests, but it is the most logical
                # way to distinguish two or more otherwise identical actions.
                try:
                    action, stash_index = action.split(':')
                except ValueError:
                    stash_index = 0

                # Closure cus component_name is reassigned
                def get_visitor_filter(component_name):
                    return lambda visitor: visitor.endswith(component_name)

                pinboard.post(
                        action=action,
                        payload=payload,
                        sender=component_name,
                        visitor_filter=get_visitor_filter(component_name),
                        enforce=True,
                        position=pinboard.LAST,
                        )

    def load_components(self):
        # Map all component identifiers to component types.
        # Component types will probably load their module.

        for component, actions in self.configuration.items():
            self.components.append(Component(component, actions))

    
    def invoke(self):
        # Invoke components functions until no new pins are added to the pinboard

        pinboard = pinboards.get_pinboard('components')
        
        all_components_processed = False
        new_pins = len(pinboard.pins)
        iteration = 0

        while not all_components_processed or new_pins > 0:
            # Keep track of iteration for informative user messages
            iteration += 1

            # If last iteration didn't result in any new pins
            # this will be the last chance for components to
            # process their pins: A deferral-attempt will raise
            # RuntimeError.
            last_chance = not new_pins

            fuse.log.info(
                    ("[Iteration {iteration}] new_pins={new_pins}, "
                     "all_components_processed={all_components_processed}, "
                     "last_chance={last_chance}").format(
                        iteration=iteration,
                        all_components_processed=all_components_processed,
                        last_chance=last_chance,
                        new_pins=new_pins,
                        )
                    )

            # Assume all components configured.
            all_components_processed = True

            # Store number of pins before configure components
            pinboard_length = len(pinboard.pins)

            # Configure all components in defined order.
            for component in self.components:
                try:
                    component_processed = component.invoke(last_chance=last_chance)
                except CaughtSignal as e:
                    print(e)
                    fuse.log.info("Exit")
                    sys.exit(1)

                fuse.log.info(
                        "Invoked component `{component}` (processed={processed})".format(
                            component=component.name,
                            processed=component_processed,
                            ))

                if component_processed:
                    fuse.log.info(
                            "All current pins processed by component `{component}`".format(
                                component=component.name,
                                ))
                else:
                    fuse.log.info(
                            "Not all current pins processed by component `{component}`".format(
                                component=component.name,
                                ))
                    all_components_processed = False


            # Check if pinboard has new pins
            new_pins = len(pinboard.pins) - pinboard_length


    def write(self):
        # Write to disk
        for f in files.get_files():
            f.write()


class Component(object):
    """
    Load modules.
    Invoke module functions (a.k.a. actions)
    """

    def __init__(self, name, actions):
        # Load module
        self.actions = actions
        self.name = name
        self.module = importlib.import_module('fuse.components.%s' % name)
        self.processed_pins = []

        fuse.log.info("component `{name}` loaded".format(name=name))

    def invoke(self, last_chance=False):
        """
        Invoke functions sequentially in order.

        Return true if all pins were processed (i.e. none was deferred).

        `last_chance` is for making error tracking much easier when writing components.

        Parameter `last_chance` will be set to True if all pins were processed last
        iteration which forbids deferrals by raising runtime exception.
        This is to prevent infinite loops when actions are unable to process pins.

        User can trigger deferral by hitting ctrl-D. User-triggered deferrals bypass
        last_chance.
        """


        pinboard = pinboards.get_pinboard('components')
        component_processed = True

        while True:
            try:
                pin_id, pin = pinboard.get(exclude=self.processed_pins)
            except StopIteration:
                fuse.log.info("all functions invoked for `{name}`".format(name=self.name))
                break

            if not pin.visitor_filter(self.module.__name__):
                continue

            try:
                try:
                    getattr(self.module, pin.action)(payload=pin.payload)
                except AttributeError:
                    if pin.enforce:
                        fuse.log.error("pin `{pin}`: component {component} could not invoke action `{action}`".format(
                            component=self,
                            action=pin.action,
                            pin=pin,
                        ))
                        raise
                finally:
                    fuse.log.error("pin `{pin}`: component {component} could not invoke action `{action}`".format(
                            component=self,
                            action=pin.action,
                            pin=pin,
                        ))

                self.processed_pins.append(pin_id)
            except EOFError:
                print('EOF')
                component_processed = False
                fuse.log.info(
                    "Pin `{module}/{action}` deferred by user (received EOF)".format(
                        module=self,
                        action=pin.action,
                    ))
                continue
            except pinboards.PinNotProcessed:
                component_processed = False
                fuse.log.info(
                    "Pin `{module}/{action}` deferred (last_chance={last_chance})".format(
                        module=self,
                        action=pin.action,
                        last_chance=last_chance,
                    )
                )
                if last_chance:
                    fuse.log.error(
                            "Pin `{module}/{action}` could not be processed.".format(
                                visitor=self,
                                action=pin.action,
                                )
                            )
                    raise

        return component_processed

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name
