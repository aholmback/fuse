import sqlite3
import semantic_version
import os
from urllib.request import urlopen
from urllib.error import HTTPError
from jinja2 import Template

def load(service, config):
    conn = sqlite3.connect('synthesis.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    t = (service,)

    result = c.execute("""SELECT
                         resource,
                         from_version,
                         to_version,
                         target,
                         content_source
                         FROM resources 
                         WHERE service=?""", t)

    def in_version_span(sample, span):
        if sample is None:
            return True

        sample = semantic_version.Version(sample)
        span = [point if point is None else semantic_version.Version(point) for point in span]

        return (span[0] is None or span[0] <= sample) and (span[1] is None or span[1] >= sample)

    # Filter out all non-applicable versions and sort the remaining entries
    # by key 'from_version' (priority will be correlated with key 'from_version').
    result = sorted(
        filter(
            lambda row: in_version_span(
                config.get('version', None),
                (row['from_version'], row['to_version'])
            ),
            result
        ),
        key=lambda row: row['from_version'],
        reverse=True,
    )

    # Add resources and ignore successive duplicates
    resources = {}
    for row in result:
        if row['resource'] in resources:
            continue

        resources[row['resource']] = Resource(
            name=row['resource'],
            service=service,
            content_source=row['content_source'],
            target=row['target'],
            config=config,
        )

    return resources

class Resource():
    def __init__(self, name, service, content_source, target, config):
        self.name = name
        self.service = service
        self.config = config

        self.target = Template(target).render(**self.config)
        self.content_source = Template(content_source).render(**self.config)
        self.content = self.get_content(self.content_source)

    def get_content(self, content_source):
        if content_source is None:
            return ''

        try:
            content = urlopen(content_source).read()
        except HTTPError:
            raise

        return Template(content.decode('utf-8')).render(**self.config)

    def write(self):
        cwd = self.config['current_working_directory']
        absolute_target = os.path.join(cwd, self.target)

        try:
            os.makedirs(os.path.dirname(absolute_target))
        except FileExistsError:
            pass

        with open(absolute_target, 'w') as fp:
            fp.write(self.content)

