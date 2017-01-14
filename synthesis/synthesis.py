import os
from jinja2 import Template
from synthesis.cli.prompts import DefaultPrompt
from synthesis.util.service import Service
from synthesis.services_available import *

use_sample_response = True

def run():
    # Instantiate all services
    services = [cls() for cls in Service.__subclasses__()]

    # Register all services
    for service in services:
        service.register()

    # Configure all services
    for service in services:
        if use_sample_response:
            service.configure(service.form_sample_response)
        else:
            config = {}
            render_keys = ['message', 'default_value', 'help_text']

            for entry in service.form:
                if entry.get('disabled', False):
                    continue

                for render_key in render_keys:
                    if not entry[render_key] is None:
                        entry[render_key] = Template(entry[render_key]).render(**config)

                user_input = DefaultPrompt(**entry).input
                config[entry['identifier']] = user_input

            service.configure(config)

    # Dispatch all services
    for service in services:
        service.dispatch()

    # Write to disk
    for service in services:
        service.write()



def configure_services(service_modules, context):
    for service_module in service_modules:
        service_module.configure(context)
