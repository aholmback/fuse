from __future__ import absolute_import, division, print_function, unicode_literals
import os
import sys
import importlib
import json
import collections
import inflection
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

        # Components are constitutional
        self.components = []

        # Parse configuration
        # Accept filename (without extension) as source
        # TODO: Implement http and local path
        configuration_source = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'lineups',
            '%s.json' % configuration,
        )

        with open(configuration_source) as f:
            self.configuration = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(f.read())

    def fuse(self):
        """
        Fuse is alias for read->invoke->write (single point entry)
        """
        self.read()
        self.invoke()
        self.write()

    def read(self):
        # Post all actions in configuration to pinboard
        # Don't load the components
        pinboard = pinboards.get_pinboard('components')
        
        for component_name, actions in self.configuration.items():
            for action, payload in actions.items():
                # When an action is queued more than once an identifier must exist
                # that prevents the action identifiers from clashing.
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
                    return lambda visitor: visitor.name == component_name

                pinboard.post(
                        action=action,
                        payload=payload,
                        sender=component_name,
                        visitor_filter=get_visitor_filter(component_name),
                        enforce=True,
                        position=pinboard.LAST,
                        )

        # Map all component identifiers to component types.
        # Component types will probably load their module.

        for component, actions in self.configuration.items():
            self.components.append(Component(component, actions))

    
    def invoke(self):
        # Invoke component functions until no new pins are added to the pinboard

        # Give components a heads up before processing pinboard
        for component in self.components:
            component.pre_process()

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
                component_processed = component.invoke(last_chance=last_chance)

                if component_processed:
                    fuse.log.info(
                            "all current pins processed by component `{component}`".format(
                                component=component.name,
                                ))
                else:
                    all_components_processed = False
                    fuse.log.info(
                            "not all current pins processed by component `{component}`".format(
                                component=component.name,
                                ))


            # Check if pinboard has new pins
            new_pins = len(pinboard.pins) - pinboard_length

    def write(self):
        # Write to disk
        for identifier, f in files.get_files().items():
            f.write()

        # Give components a heads up after processing pinboard
        for component in self.components:
            component.post_process()


class Component(object):
    """
    Load module
    Instantiate class
    Invoke module functions (a.k.a. actions)
    """

    def __init__(self, name, actions):
        self.actions = actions
        self.name = name
        self.processed_pins = []

        # Load module
        self.module = importlib.import_module('fuse.components.%s' % name)

        # Instantiate class
        class_name = inflection.camelize(name)
        self.instance = getattr(self.module, class_name)(self.name)

        fuse.log.info("component `{name}` loaded".format(name=name))

    def pre_process(self):
        self.instance.pre_process()

    def post_process(self):
        self.instance.post_process()

    def invoke(self, last_chance=False):
        """
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

            # Get next pin, exit on StopIteration
            try:
                pin_id, pin = pinboard.get_next(exclude=self.processed_pins)
            except StopIteration:
                break

            # Verify that component is recipient (usually it is)
            if not pin.visitor_filter(self.instance):
                continue

            # Invoke component action
            try:
                getattr(self.instance, pin.action)(payload=pin.payload)
                self.processed_pins.append(pin_id)
            except AttributeError:
                # Method does not exist (exit on enforce==True, ignore otherwise)
                if not hasattr(self.instance, pin.action):
                    if pin.enforce is True:
                        fuse.log.error(
                            "pin `{pin}` says enforce is True but component `{component}` doesn't implement action `{action}`".format(
                            component=self,
                            action=pin.action,
                            pin=pin,
                        ))
                        sys.exit(1)
                    else:
                        continue
                else:
                    # Invoked method raised AttributeError
                    raise
            except TypeError: # Signature mismatch (reraise)
                fuse.log.error("pin `{pin}`: component {component} implement `{action}` but signature doesn't match".format(
                    component=self,
                    action=pin.action,
                    pin=pin,
                ))
                raise
            except EOFError: # User hit ctrl-D (EOF)
                print('EOF')
                component_processed = False
                fuse.log.info(
                    "Pin `{module}/{action}` deferred by user (received EOF)".format(
                        module=self,
                        action=pin.action,
                    ))
                continue
            except CaughtSignal as e: # User hit ctrl-C (SIGTERM)
                print(e)
                fuse.log.info("Exit")
                sys.exit(1)
            except pinboards.PinNotProcessed: # Invoked method raised PinNotProcessed
                component_processed = False

                # Components are not allowed to defer if last_chance is True
                if last_chance:
                    fuse.log.error(
                            "Pin `{component}/{action}` could not be processed.".format(
                                component=self,
                                action=pin.action,
                                )
                            )
                    raise


                fuse.log.info(
                    "Pin `{module}/{action}` deferred (last_chance={last_chance})".format(
                        module=self,
                        action=pin.action,
                        last_chance=last_chance,
                    )
                )

        return component_processed

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name
