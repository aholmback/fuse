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



    def get_inbox(self, channel):

        def inbox(sender, **kw):
            self.queues[channel].put((
                sender,
                kw['payload'],
            ))

        return inbox

    def send_message(self, channel, payload):
        signal = self.message_dispatcher.signal(channel)
        signal.send(self.name, payload=payload)

    def get_message(self, channel):
        if self.queues[channel].empty():
            raise IndexError("No messages in channel %s" % channel)

        sender, payload = self.queues[channel].get()
        self.config[channel] = payload

        return payload

    def prompt(self, prompt_key, config_key=None, overwrite=False, **parameters):

        # Config identifier should be the same as prompt identifier unless otherwise specified
        if config_key is None:
            config_key = prompt_key

        # If config identifier is not None av overwrite is False, skip prompting and return existing value
        if self.config.get(config_key, None) is not None and not overwrite:
            return self.config[config_key]

        # Fill in empty parameters from persistent storage if present
        try:
            default_parameters = self.prompts.get(identifier=prompt_key)

            for p in ['text', 'description', 'default', 'validators', 'options']:
                parameters.setdefault(p, getattr(default_parameters, p))

        except self.prompts.DoesNotExist:
            pass

        # Replace validator descriptors with actual functions
        if parameters.get('validators', None) is None:
            parameters['validators'] = []
        else:
            parameters['validators'] = [getattr(self.validators, validator) for validator in parameters['validators'].split(',')]

        # Split options to list
        if parameters.get('options', None) is not None:
            parameters['options'] = parameters['options'].split(',')

        # Store input value under designate key and return the value
        self.config[config_key] = self.prompter(identifier=prompt_key, **parameters).input
        return self.config[config_key]

    def instantiate(self):
        pass

    def configure(self):
        pass

    def write(self):
        pass
