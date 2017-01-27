from fuse.utils import validators as validator_functions
import six
import fuse

class InvalidInputError(Exception):
    pass

def prompt(
        text='', description='',
        validators=None, options=None,  default=None,
        pre_validation_hook=None, post_validation_hook=None):
    """
    Present an informative message to the user and return input from user
    """

    # Set pre/post validation hook to return-input lambdas if None
    if pre_validation_hook is None:
        pre_validation_hook = lambda v: v

    if post_validation_hook is None:
        post_validation_hook = lambda v: v

    # Context for prompt template
    context = {
            'text': text,
            'default': default,
            'options': options,
            'description': description,
            'invalid_input_message': None,
            }

    # Replace validator descriptors with actual functions
    if validators is None:
        validators = []

    validators = [getattr(validator_functions, validator) for validator in validators]

    # If options is a list with elements, create a validator on the
    # fly and replace all other potential validators.
    if options is not None:
        option_validator = lambda v: v in [identifier for identifier, _ in options]
        option_validator.__doc__ = "Value must be an integer in [1-{options_length}]".format(options_length=len(options))
        validators = [option_validator]
    else:
        # Force None and empty string ('') to fail
        validators.insert(0, validator_functions.not_none)

    def read_input():
        # Return default value if confirm is False and default is not None
        if fuse.settings['confirm'] is False and default is not None:
            return default

        user_message = fuse.render(context, 'prompt.j2', out=None).strip()

        # Set input function (python 3's input is equal to python 2's raw_input)
        return (raw_input if six.PY2 else input)(user_message)

    def map_input(user_input):
        # Assumption: If a default value exists, it is already mapped
        if default is not None and user_input in ('', None):
            return default

        if options:
            try:
                option_index = int(user_input) - 1
                if option_index >= 0:
                    user_input = options[option_index][0]
                else:
                    user_input = None
            except (TypeError, IndexError, ValueError):
                user_input = None

        return user_input

    def validate_input(user_input):
        user_input = pre_validation_hook(user_input)

        for validator in validators:
            if not validator(user_input):
                context['invalid_input_message'] = validator.__doc__.strip()
                raise InvalidInputError

        return post_validation_hook(user_input)

    while True:
        try:
            # Read
            user_input = read_input()
            fuse.log.info("got user input `{user_input}`".format(user_input=user_input))

            # Map
            user_input = map_input(user_input)
            fuse.log.info("user input converted to `{user_input}` (by input map)".format(
                user_input=user_input, map_input=map_input))

            # Validate
            user_input = validate_input(user_input)
            fuse.log.info("user input converted to `{user_input}` (by input validation)".format(
            user_input=user_input))

            return user_input

        except InvalidInputError:
            pass

