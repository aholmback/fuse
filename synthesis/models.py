from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
import datetime
import os
from jinja2 import Template
from urllib.request import urlopen
from urllib.error import HTTPError

db = SqliteExtDatabase('synthesis.db')

class BaseModel(Model):
    class Meta:
        database = db

class Resource(BaseModel):
    identifier = CharField()
    service = CharField()
    from_version = CharField(null=True)
    to_version = CharField(null=True)
    target = CharField()
    content_source = CharField(null=True)

    def write(self, context):
        if self.content_source is None:
            content = ''
        else:
            content_source = self.content_source.format(**context)
            content = urlopen(content_source).read().decode('utf-8')
            content = Template(content).render(**context)

        target = self.target.format(**context)
        absolute_target = os.path.join(
            context['current_working_directory'],
            target
        )

        try:
            os.makedirs(os.path.dirname(absolute_target))
        except FileExistsError:
            pass

        with open(absolute_target, 'w') as fp:
            fp.write(content)


class Prompt(BaseModel):
    identifier = CharField()
    text = CharField(null=True)
    description = CharField(null=True)
    default = CharField(null=True)
    validators = CharField(null=True)
    options = CharField(null=True)


def data():
    resources = (
        {
            'identifier': 'settings',
            'service': 'django',
            'from_version': '1.10.1',
            'to_version': None,
            'target': '{project_name}/settings.py',
            'content_source': ('https://raw.githubusercontent.com/djan'
                               'go/django/{django_version}/django/conf'
                               '/project_template/project_name/setting'
                               's.py-tpl'),
        },
        {
            'identifier': 'init',
            'service': 'django',
            'from_version': '1.10.1',
            'to_version': None,
            'target': '{project_name}/__init__.py',
            'content_source': ('https://raw.githubusercontent.com/djan'
                               'go/django/{django_version}/django/conf'
                               '/project_template/project_name/__init_'
                               '_.py-tpl'),
        },
        {
            'identifier': 'urls',
            'service': 'django',
            'from_version': '1.10.1',
            'to_version': None,
            'target': '{project_name}/urls.py',
            'content_source': ('https://raw.githubusercontent.com/djan'
                               'go/django/{django_version}/django/conf'
                               '/project_template/project_name/urls.py'
                               '-tpl'),
        },
        {
            'identifier': 'wsgi',
            'service': 'django',
            'from_version': '1.10.1',
            'to_version': None,
            'target': '{project_name}/wsgi.py',
            'content_source': ('https://raw.githubusercontent.com/djan'
                               'go/django/{django_version}/django/conf'
                               '/project_template/project_name/wsgi.py'
                               '-tpl'),
        },
        {
            'identifier': 'manage',
            'service': 'django',
            'from_version': '1.10.1',
            'to_version': None,
            'target': 'manage.py',
            'content_source': ('https://raw.githubusercontent.com/djan'
                               'go/django/{django_version}/django/conf'
                               '/project_template/manage.py-tpl'),
        },
        {
            'identifier': 'requirements',
            'service': 'pip',
            'from_version': None,
            'to_version': None,
            'target': 'requirements.txt',
            'content_source': None,
        },
        )

    for resource in resources:
        Resource.create(**resource)

    prompts = (
        {
            'identifier': 'project_name',
            'text': "Project Name",
            'description': None,
            'default': None,
            'validators': None,
            'options': None,
        },
        {
            'identifier': 'project_slug',
            'text': "Project Slug",
            'description': None,
            'default': None,
            'validators': 'variable_name',
            'options': None,
        },
        {
            'identifier': 'semantic_version',
            'text': "Version (semantic)",
            'description': None,
            'default': None,
            'validators': 'semantic_version',
            'options': None,
        },
        {
            'identifier': 'directory',
            'text': "Directory",
            'description': None,
            'default': None,
            'validators': 'creatable_dir,writable_dir,empty_dir',
            'options': None,
        },
    )

    for prompt in prompts:
        Prompt.create(**prompt)

if __name__ == '__main__':
    try:
        db.create_tables([Prompt, Resource])
        data()
    except OperationalError:
        print("Didn't create or do anything cus stuff already exist")

