
class SettingsNode:
    def __init__(self, dict: dict) -> None:
        for a, b in dict.items():
            if isinstance(b, (list, tuple)):
               setattr(self, a, [SettingsNode(x) if isinstance(x, type(dict)) else x for x in b])
            else:
               setattr(self, a, SettingsNode(b) if isinstance(b, type(dict)) else b)

    def getattrORdef(self, attr_name: str, default):
        for attr in dir(self):
            if attr == attr_name:
                return attr_name

        return default