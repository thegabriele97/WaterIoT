import copy
import logging

class SettingsNode:

    def __init__(self, dict: dict, logger: logging) -> None:

        self._logger = logger;

        for a, b in dict.items():
            if isinstance(b, (list, tuple)):
               setattr(self, a, [SettingsNode(x, logger) if isinstance(x, type(dict)) else x for x in b])
            else:
               setattr(self, a, SettingsNode(b, logger) if isinstance(b, type(dict)) else b)

    def getattr(self, attr_name: str):

        if "." in attr_name:
            return SettingsNode.getattr(getattr(self, attr_name.split('.')[0]), '.'.join(attr_name.split('.')[1:]))

        for attr in dir(self):
            if attr == attr_name:
                return getattr(self, attr)

        self._logger.error(f"Attribute {attr_name} not found in settings")
        raise ValueError(f"Attribute {attr_name} not found in settings")

    def getattrORdef(self, attr_name: str, default):

        if "." in attr_name:
            return SettingsNode.getattrORdef(getattr(self, attr_name.split('.')[0]), '.'.join(attr_name.split('.')[1:]), default)

        for attr in dir(self):
            if attr == attr_name:
                return getattr(self, attr)

        return default

    def toDict(self):
        return {k: v for k, v in self.__dict__.items() if k[0] != '_'}
    