from errors import SettingsError
import json

class Settings:

    def __init__(self, filename=None):
        if filename is None: raise SettingsError("No settings file provided!")
        with open(filename) as f: self._settings = json.loads(f.readline())
        self._filename = filename
        self._version = 0

    def set(self, key, value):
        if key not in self._settings:
            raise SettingsError("key '{key}' not found in settings")
        self._settings[key] = value
        with open(self._filename, "w") as f: f.write(json.dumps(self._settings))

    def get(self, key):
        if key not in self._settings:
            raise SettingsError("key '{key}' not found in settings")
        return self._settings[key]