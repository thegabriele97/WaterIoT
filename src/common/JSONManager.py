import json
from re import A

class JSONManager:

    def __init__(self, filename: str, autosave: bool = True, structure_mod_allowed: bool = False) -> None:

        with open(filename, "r") as fp:
            self._d = json.load(fp)

        self._autosave = autosave
        self._structure_mod_allowed = structure_mod_allowed
        self._filename = filename

    def get(self, path: str):
        """
        Path between keys of the dictionary.
        Must start with a /
        """

        if len(path) == 0 or path[0] != '/':
            raise ValueError("Path must begin with a /")

        if path[-1] != "/":
            path = str(path + "/")

        return JSONManager._intget(path, self._d)

    def set(self, path: str, value) -> None:
        """
        Path between keys of the dictionary.
        Must start with a /
        """

        if len(path) == 0 or path[0] != '/':
            raise ValueError("Path must begin with a /")

        if path[-1] != "/":
            path = str(path + "/")
        
        tomod = JSONManager._intget(path, self._d)

        # checking if we are modifying to dict, they must be the same to allow so
        signalit = False
        if isinstance(tomod, dict) and isinstance(value, dict):
            # checking same keys
            if not all(k in tomod for k in value) or not all(k in value for k in tomod):
                signalit = True

            # checking same value type
            if not JSONManager._rec_check_type(tomod, value) or not JSONManager._rec_check_type(value, tomod):
                signalit = True

            signalit = signalit and not self._structure_mod_allowed
            if signalit:
                raise ValueError("Modifiyng the structure of a JSON is not allowed!")

        elif (signalit or isinstance(tomod, dict) or isinstance(value, dict) or type(tomod) is not type(value)) and not self._structure_mod_allowed:
            raise ValueError("Modifiyng the structure of a JSON is not allowed!")

        JSONManager._intset(path, self._d, value)
        with open(self._filename, "w") as fp:
            fp.write(json.dumps(self._d, indent=4))

    @staticmethod
    def _rec_check_type(tomod: dict, value: dict) -> bool:

        if not all(isinstance(tomod[k], type(value[k])) for k in [k for k in tomod if k in value]):
            return False

        if not all(JSONManager._rec_check_type(tomod[k], value[k]) for k in [k for k in tomod if k in value] if isinstance(tomod[k], dict)):
            return False

        return True

    @staticmethod
    def _intget(path: str, d: dict) -> dict:
        
        if len(path) == 0 or path == "/":
            return d

        p = path.split("/")
        return JSONManager._intget(path[path.index("/", 1):], d[p[1]])

    @staticmethod
    def _intset(path: str, d: dict, value) -> None:
        
        if len(path) == 0 or path == "/":
            d = value
            return

        p = path.split("/")
        newp = path[path.index("/", 1):]
        if len(newp) == 0 or newp == "/":
            d[p[1]] = value
            return

        JSONManager._intset(newp, d[p[1]], value)
