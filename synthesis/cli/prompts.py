from cement.utils.shell import Prompt
from .validators import not_none

class DefaultPrompt(Prompt):
    class Meta:
        max_attempts = 99
        auto = True

    def __init__(
            self,
            identifier,
            message,
            help_text,
            default_value,
            validators,
            retry,
            post_process=None,
    ):

        self.identifier = identifier
        self.validators = [not_none]
        self.post_process = post_process

        if validators:
            self.validators += validators

        if not default_value is None:
            message += " (default: %s)" % default_value

        message += ":"

        super().__init__(text=message, default=default_value)

    def process_input(self):
        if self.post_process:
            self.input = self.post_process(self.input)

    def is_valid(self, value):
        return all(validator(value) for validator in self.validators)

    def get_validation_text(self):
        rules = [validator.__doc__.strip() for validator in self.validators if validator.__doc__]

        return '\n'.join(["%i) %s" % (i+1, rule) for i, rule in enumerate(rules)])

    def prompt(self):
        """
        Prompt the user, and store their input as `self.input`.
        """

        attempt = 0
        while not self.is_valid(self.input):
            if attempt >= int(self._meta.max_attempts):
                if self._meta.max_attempts_exception is True:
                    raise FrameworkError("Maximum attempts exceeded getting "
                                         "valid user input")
                else:
                    return self.input

            attempt += 1
            self._prompt()

            if not self.is_valid(self.input):
                if attempt == 1:
                    self._meta.text = self.get_validation_text() + '\n' + self._meta.text
                continue
            elif self._meta.options is not None:
                if self._meta.numbered:
                    try:
                        self.input = self._meta.options[int(self.input) - 1]
                    except (IndexError, ValueError) as e:
                        self.input = None
                        continue
                else:
                    if self._meta.case_insensitive is True:
                        lower_options = [x.lower()
                                         for x in self._meta.options]
                        if not self.input.lower() in lower_options:
                            self.input = None
                            continue
                    else:
                        if self.input not in self._meta.options:
                            self.input = None
                            continue

        self.process_input()
        return self.input
