import os
import importlib
import inflection
import blinker
import queue
import jinja2
from synthesis.utils import prompts, validators
from synthesis.recipes import django_minimal
from synthesis.models import Prompt, Resource

def run():
    recipe = django_minimal.recipe
    services = []

    # Instantiate services
    for entry in recipe:
        service_module_name, = entry.keys()
        service_class_name = inflection.camelize(service_module_name)
        service_module = importlib.import_module('synthesis.services.%s' % service_module_name)

        service = getattr(service_module, service_class_name)(
            name=service_module_name,
            config=entry[service_module_name],
            queuer=queue.Queue,
            message_dispatcher=blinker,
            template_engine=jinja2.Template,
            prompter=prompts.DefaultPrompt,
            prompts=Prompt,
            resources=Resource,
            validators=validators,
        )

        # TODO: Find out why this works but the same 3 rows moved to Service.__init__ fails.
        for channel in service.listens_to:
            service.queues[channel] = queue.Queue()
            service.message_dispatcher.signal(channel).connect(service.inbox)

        service.instantiate()
        services.append(service)

    # Configure services
    for service in services:
        service.collect()

    for service in services:
        pass

    # Write to disk
    for service in services:
        service.write()

