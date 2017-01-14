from synthesis.util import resources

class Service:

    def __init__(self):
        self.name = type(self).__name__.lower()
        self.resources = {}

    def register(self):
        raise NotImplementedError

    def configure(self):
        raise NotImplementedError

    def dispatch(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError

    def load_resources(self):
        self.resources = resources.load(self.name, self.config)
        print(self.resources)

    def write_resources(self, cwd):
        for resource_name, resource in self.resources.items():
            resource.write(self.cwd)
