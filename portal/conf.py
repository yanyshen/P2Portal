import json
import os.path, sys
from os.path import join

DEFAULT_CONF_PATH = os.path.join(os.path.dirname(__file__), 'repo/static/portal.conf')

class PortalConfig(object):

    def __init__(self, conf_path=DEFAULT_CONF_PATH):
        self.reload(conf_path)

    def reload(self, conf_path=None):
        if conf_path:
            self.conf_path = conf_path
        with open(self.conf_path) as file:
            self.conf_data = json.load(file)

    def get(self, name):
        result = self.conf_data.get(name) 
        return result

    def set(self, name, value):
        self.conf_data[name] = value

    def save(self):
        with open(self.conf_path, 'w') as file:
            json.dump(self.conf_data, file, sort_keys=True, indent=4)


CONF = PortalConfig(DEFAULT_CONF_PATH)
