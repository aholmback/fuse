from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component

class Docker(Component):

    def service_dependency(self, payload):
        """
        Expected payload structure:
        payload = {
            'name': service name (used as label in docker)
            'version': service version (can be empty)
            'uri': Complete resource identifier (schema://user:password@ip-address:port/)
            'extra_ports': list of extra ports
            }
        """
        if 'docker_directory' not in self.context:
            raise self.PinNotProcessed

        self.context.setdefault('services', [])
        self.context['services'].append(
        )

        self.files(
            component=self.name,
            identifier='docker-compose',
            render=self.render,
            path='{docker_directory}/docker-compose.yml',
            context=self.context,
        )

    def docker_directory(self, payload):
        if 'project_home' not in self.context:
            raise self.PinNotProcessed

        payload = payload.format(**self.context)

        self.context['docker_directory'] = self.prompt(
            text="Directory for docker compose",
            default=payload or self.context['project_home'],
            validators=['creatable_path','writable_directory','empty_directory'],
            pre_validation_hook=os.path.expanduser,
        )

