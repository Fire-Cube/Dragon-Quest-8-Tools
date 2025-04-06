from enum import Enum
from pathlib import Path


def read_file(file_path: Path) -> bytes:
    with open(file_path, "rb") as f:
        return f.read()
    

def fix_umlaute(text: str) -> str:
    text = text.replace("<:a>", "ä")
    text = text.replace("<:A>", "Ä")
    text = text.replace("<:o>", "ö")
    text = text.replace("<:O>", "Ö")
    text = text.replace("<:u>", "ü")
    text = text.replace("<:U>", "Ü")

    text = text.replace("<ss>", "ß")
    return text


class UNIT_CATEGORY:
	UNKNOWN = -1,
	MONSTER = 0,
	MONSTER_EX = 1,
	ANIMAL = 2,
	SPECIAL = 3,
	NPC = 4,
	HERO = 5


def get_unit_category(unit_id: int) -> str:
    if 100 <= unit_id < 500:
        return UNIT_CATEGORY.MONSTER
    
    elif 500 <= unit_id < 601:
        return UNIT_CATEGORY.MONSTER_EX
    
    elif 601 <= unit_id < 801:
        return UNIT_CATEGORY.ANIMAL
    
    elif 801 <= unit_id < 901:
        return UNIT_CATEGORY.SPECIAL
    
    elif 901 <= unit_id < 1000:
        return UNIT_CATEGORY.NPC
    
    elif 1000 <= unit_id <= 1003:
        return UNIT_CATEGORY.HERO
    
    else:
        return UNIT_CATEGORY.UNKNOWN
    

class SafeEnum(Enum):
    @classmethod
    def _missing_(cls, value):
        # Wenn der Wert nicht definiert ist, erzeuge ein "virtuelles" Enum-Member
        pseudo_member = object.__new__(cls)
        pseudo_member._value_ = value
        pseudo_member._name_ = str(value)
        return pseudo_member


    def __str__(self):
        # Gibt entweder den Namen oder den numerischen Wert zurück, wie in C#
        if self._name_ != str(self._value_):
            return self._name_
        
        return str(self._value_)