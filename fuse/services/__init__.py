from __future__ import absolute_import, division, print_function, unicode_literals
from fuse import models

class Service:

    listens_to = []

    def __init__(self,
                 name,
                 config,
                 queuer,
                 message_dispatcher,
                 template_engine,
                 prompter,
                 prompts,
                 resources,
                 validators,
                 ):

        self.name = name
        self.config = config
        self.queuer = queuer
        self.message_dispatcher = message_dispatcher
        self.template_engine = template_engine
        self.prompter = prompter
        self.prompts = prompts
        self.resources = resources
        self.validators = validators

        self.queues = {}

    def inbox(self, sender, channel, payload):
        self.queues[channel].put((
            sender,
            payload,
        ))

    def send_message(self, channel, payload):
        signal = self.message_dispatcher.signal(channel)
        signal.send(self.name, payload=payload, channel=channel)

    def get_message(self, channel):
        if self.queues[channel].empty():
            raise IndexError("No messages in channel %s" % channel)

        sender, payload = self.queues[channel].get()
        self.config[channel] = payload

        return payload

    def prompt(self, identifier, **parameters):


        # Fill in empty parameters from persistent storage if present
        try:
            default_parameters = self.prompts.get(identifier=identifier)

            for p in ['text', 'description', 'default', 'validators', 'options']:
                parameters.setdefault(p, getattr(default_parameters, p))

        except self.prompts.DoesNotExist:
            pass

        # Replace validator descriptors with actual functions
        if parameters.get('validators', None) is None:
            parameters['validators'] = []
        else:
            parameters['validators'] = [getattr(self.validators, validator) for validator in parameters['validators'].split(',')]

        # Split options to list if it's a string
        if type(parameters.get('options', None)) is str:
            parameters['options'] = parameters['options'].split(',')


        # Set the default value to current config (if present)
        parameters['default'] = self.config.get(identifier, None) or parameters['default']

        # Setup prompter and set its input value
        prompter = self.prompter(identifier=identifier, **parameters)
        prompter.input = self.config.get(identifier, None)

        prompter.prompt()

        # Store input value under designate key and return the value
        self.config[identifier] = prompter.input
        return prompter.input

    def write(self):
        result = models.Resource.select().where(models.Resource.service == self.name)

        def in_version_span(sample, span):
            if sample is None:
                return True

            sample = semantic_version.Version(sample)
            span = [point if point is None else semantic_version.Version(point) for point in span]

            return (span[0] is None or span[0] <= sample) and (span[1] is None or span[1] >= sample)

        # Filter out all non-applicable versions and sort the remaining entries
        # by key 'from_version' (priority will be correlated with key 'from_version').

        resources = []
        for row in result:
            if not in_version_span(self.config.get('version', None), (row.from_version, row.to_version)):
                continue
            resources.append(row)

        resources.sort(
            key=lambda row: row.from_version,
            reverse=True,
        )

        for resource in resources:
            resource.write(self.config)


    def instantiate(self):
        pass

    def collect(self):
        pass

    def configure(self):
        pass

