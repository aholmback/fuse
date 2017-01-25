from __future__ import absolute_import, division, print_function, unicode_literals
import os, sys

class Component(object):
    """
    Abstract base class for components

    Create a component by subclassing this class and extend it by
    adding listeners.

    Fuse configures components by sequentially calling the following
    methods for one component at the time:
        + setup
        while all_components_configured is False:
            + configure
        + write
        + finalize

    Method `finalize` is only a placeholder for custom post-write actions
    (like creation of virtualenv or pip installs). The other methods should
    not be extended.

    List of globally meaningful listeners

    Method                  Payload type    Payload Description
    ======                  ============    ===================
    project_home            string          Directory for project files
    project_name            string          Human-friendly project name
    project_slug            string          Identifier-friendly project name
    no_version_control      string          Path (relative to project home)
    global_setting          dict            Key/value + tier
    python_dependency       string          String identifying a python requirement
    service_dependency      string          Url identifying a service requirement
    os_depency              string          String identifying an os requirement
    deployment_tiers        list of strings List of environments (dev, stage, prod etc)

    """

    def __init__(self, name, logger, render):

        # Name of component module (file name without .py)
        self.name = name

        # Application wide logger.
        # Usage: logger.info([message])
        self.logger = logger

        # Render function provided by application wide instance of 
        # jinja2 template engine.
        # Usage: render(context, template, out=[file-like object])
        # Set out=None to prevent output
        self.render = render

        # A list of pin identifiers that has been processed by the component.
        # Prevents already processed pins from being processed again.
        self.processed_pins = []

        # Component-specific context. Used primarily for template
        # substitution but can be used for all kinds of component
        # wide resources as long as keys and values are strings.
        self.context = {}

        # List of contexts to provide automatic support for retriggers.
        # When retriggering a component, the current context needs to
        # be appended to context stash before it gets overwritten.
        self.context_stash = []

        # Files that will be written to disk during write().
        # Key: Target path
        # Value: File content
        #
        # If target path ends with a dash and content is null,
        # only an empty directory will be created.
        self.files = {}

        # Contains initial actions added during setup(). Useful
        # when retriggering a new instance for the component.
        # Key: function name
        # Value: method payload (will end up in `payload` argument
        self.actions = None


    def setup(self, pinboard, actions):
        """
        Posts all actions in `actions` to pinboard

        Fuse is calling this method when loading lineup.
        """
        self.actions = actions

        for action in actions:
            payload = actions[action]
            pinboard.post(
                    action=action,
                    payload=payload,
                    sender=self,
                    handler_filter=lambda handler: handler is self,
                    enforce=True,
                    upnext=False,
                    )

    def configure(self, pinboard, prompt, last_chance=False):
        """
        Process pins from pinboard. Return true if all pins were processed
        (i.e. none was deferred).

        Parameter `last_chance` will be set to True if all pins were processed last
        iteration which forbids deferrals by raising runtime exception.
        This is to prevent infinite loops when actions are unable to process pins.

        User can trigger deferral by hitting ctrl-D. User-triggered deferrals bypass
        last_chance.
        """

        all_pins_processed = True

        while True:
            try:
                pin_id, pin = pinboard.get(exclude=self.processed_pins)
            except StopIteration:
                break

            if not pin.is_recipient(self):
                continue

            try:
                getattr(self, pin.action)(payload=pin.payload, pinboard=pinboard, prompt=prompt)
                self.processed_pins.append(pin_id)
            except EOFError:
                print('EOF')
                all_pins_processed = False
                self.logger.info(
                    "Pin `{handler}/{action}` deferred by user (received EOF)".format(
                        handler=self,
                        action=pin.action,
                    ))
                continue
            except pinboard.PinNotProcessed:
                all_pins_processed = False
                self.logger.info(
                    "Pin `{handler}/{action}` deferred (last_chance={last_chance})".format(
                        handler=self,
                        action=pin.action,
                        last_chance=last_chance,
                    )
                )
                if last_chance:
                    self.logger.error(
                            "Pin `{handler}/{action}` could not be processed.".format(
                                handler=self,
                                action=pin.action,
                                )
                            )
                    raise

        return all_pins_processed

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


