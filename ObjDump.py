from collections import OrderedDict
import json
from types import NoneType
from enum import Enum

def dump_obj(object, desired_order: list=[]):
    def serialize(object, desired_order):
        exclude = ("ptr", "byte_data", "exclude_dump")
        if hasattr(object, "exclude_dump"):
            exclude = object.exclude_dump + exclude

        if isinstance(object, Enum):
            return f"ENUM<{object.name}>"
        
        elif hasattr(object, "__dict__"):
            result = OrderedDict()

            for key in desired_order:
                if key in object.__dict__ and key not in exclude and not key.startswith("_"):
                    result[key] = serialize(object.__dict__[key], desired_order)
            
            for key, value in object.__dict__.items():
                if key not in result and key not in exclude and not key.startswith("_"):
                    result[key] = serialize(value, desired_order)

            return result
        
        
        elif isinstance(object, (list, tuple)):
            return [serialize(value, desired_order) for value in object]
        
        elif isinstance(object, dict):
            return {key: serialize(value, desired_order) for key, value in object.items()}
        
        elif isinstance(object, (bytes, bytearray)):
            return repr(object)
        
        elif isinstance(object, str):
            return object
        
        elif isinstance(object, (int, float)):
            return object
        
        elif isinstance(object, NoneType):
            return None
        
        else:
            raise Exception(f"Unsupported type: {type(object)}")

    return json.dumps(serialize(object, desired_order), indent=4, ensure_ascii=False)