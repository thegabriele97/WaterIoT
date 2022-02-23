import json
import logging
import os
import inspect

from common.SettingsNode import SettingsNode

class SettingsManager:

    @staticmethod
    def json2obj(json_filename: str, logger: logging) -> SettingsNode:
        fp = open(json_filename, "r")
        dict = json.load(fp)
        fp.close()

        return SettingsNode(dict, logger)

    @staticmethod
    def relfile2abs(file):
        return os.path.join(os.path.dirname(inspect.stack()[1].filename), file)