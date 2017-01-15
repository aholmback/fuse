from synthesis.services import Service
import os

class Home(Service):

    def configure(self):
        self.prompt('directory', text="Project Home", default=os.getcwd())
        self.send_message('current_working_directory', payload=self.config['directory'])

