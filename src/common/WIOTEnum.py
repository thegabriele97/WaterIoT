from enum import Enum

class WIOTEnum(Enum):

    @classmethod
    def value_of(cls, value):

        if value is None:
            return None

        for k, v in cls.__members__.items():
            if k == value:
                return v
        else:
            raise ValueError(f"'{cls.__name__}' enum not found for '{value}'")
