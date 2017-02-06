from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component

import six
import os
from jinja2 import Template

if six.PY2:
    from urllib2 import urlopen, HTTPError
else:
    from urllib.request import urlopen
    from urllib.error import HTTPError

class Django(Component):

    component_type = 'framework'

    def project_home(self, payload):
        self.context['project_home'] = payload

    def global_setting(self, payload):
        """
        Expected payload structure
        payload = {
            'key': setting key
            'value': setting value
            'environment': user defined deploy environment or '*'
            'type': ['string', 'number', 'function']
            }
        """
        if 'default_settings' not in self.context:
            raise self.PinNotProcessed

        self.context.setdefault('components_settings', {})
        entry_identifier = ':'.join([payload['key'], payload['environment']])

        # Disable default_settings (the content is written to context['default_settings'])
        default_settings = self.files(
            component=self.name,
            identifier='default_settings',
            write=False,
        )

        # Update settings
        self.files(
            component=self.name,
            identifier='settings',
            render=self.render,
            path=default_settings.path,
            context=self.context,
        )

        # If the setting is environment specific, wrap the key in env() and
        # post the key/value-pair (+ environment identifier) to 'environment_variable' 
        # Not that the environment variable is prefixed with project identifier (environment
        # is a global namespace)
        if not payload['environment'] == '*':
            env_key = '{prefix}_{key}'.format(
                    prefix=self.context['project_identifier'].upper(),
                    key=payload['key'],
                    )

            self.post('environment_variable', {
                'key': env_key,
                'value': payload['value'],
                'environment': payload['environment'],
            })


            payload['value'] = 'os.environ[\'%s\']' % env_key
            payload['type'] = 'function'


        self.context['components_settings'][entry_identifier] = payload
        self.context['environment'] = payload['environment']

    def project_name(self, payload):
        self.context['project_name'] = self.prompt(
            text="Human-friendly project name",
            default=payload,
        )

        self.post(
                'project_name',
                self.context['project_name'],
                visitor_filter=lambda handler: handler is not self,
                position=1,
                )

    def project_identifier(self, payload):
        if not 'project_name' in self.context:
            raise self.PinNotProcessed

        self.context['project_identifier']  = self.prompt(
            text="Project Slug",
            default=payload or re.sub('[^0-9a-zA-Z]+', '_', self.context['project_name'].lower()),
            validators=['identifier'],
        )

        self.post(
            'project_identifier',
            self.context['project_identifier'],
            visitor_filter=lambda handler: handler is not self,
            position=0,
        )

    def project_environments(self, payload):
        self.context['project_environments'] = self.prompt(
            text="Comma-separated list of environment identifiers",
            default=payload,
            validators=['identifier_list'],
            pre_validation_hook=lambda v: v.split(','),
        )

        self.post(
            'project_environments',
            self.context['project_environments'],
            visitor_filter=lambda handler: handler is not self,
            position=0,
        )

    def version(self, payload):
        self.context['version'] = self.prompt(
            text="Version (semantic)",
            default=payload,
            validators=['semantic_version'],
        )

        self.post('python_dependency', 'django==%s' % self.context['version'])

    def settings_file(self, payload):
        if 'project_environments' not in self.context:
            raise self.PinNotProcessed

        self.add_file(payload, 'default_settings', 'project_name/settings.py-tpl')

        settings_module = (payload
                           .format(**self.context)[len(self.context['project_home']):-3]
                           .strip('/')
                           .replace('/', '.')
                           )

        for environment in self.context['project_environments']:
            self.post('environment_variable', {
                'key': 'DJANGO_SETTINGS_MODULE',
                'value': settings_module,
                'environment': environment,
            })

    def init_file(self, payload):
        self.add_file(payload, 'default_project_init', 'project_name/__init__.py-tpl')

    def urls_file(self, payload):
        self.add_file(payload, 'default_urls', 'project_name/urls.py-tpl')

    def wsgi_file(self, payload):
        self.add_file(payload, 'default_wsgi', 'project_name/wsgi.py-tpl')

    def manage_file(self, payload):
        self.add_file(payload, 'default_manage', 'manage.py-tpl')

    def add_file(self, path, identifier, template):
        self.context[identifier] = self.files(
                component=self.name,
                identifier=identifier,
                render=self.http_render,
                path=path,
                context=self.context,
                template=template,
                ).content

    def http_render(self, context, template, out):
        project_template_root = 'https://raw.githubusercontent.com/django/django/{version}/django/conf/project_template/'

        template = project_template_root + template
        template = template.format(**self.context)

        try:
            content = urlopen(template).read().decode('utf-8')
        except HTTPError as e:
            self.log.error("url `{url}` not found".format(url=template))
            raise e

        return Template(content).render(
            project_name=self.context['project_identifier'],
            django_version=self.context['version'],
            docs_version='.'.join(self.context['version'].split('.')[:-1])
        )

