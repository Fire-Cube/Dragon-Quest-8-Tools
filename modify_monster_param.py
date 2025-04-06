import argparse

from pathlib import Path

from MonsterParams import MonsterParams
from Utils import read_file
from BinaryUtils import BytePtr
from MonsterParams import MonsterParamsFileHandler


def set_monster_param(monster_params_obj, monster_id, field_name, value_str):
    monster = next((monster_param for monster_param in monster_params_obj.monster_params if monster_param.monster_id == monster_id), None)
    if not monster:
        print(f"[Error] Monster with ID {monster_id} not found.")
        return False

    if not hasattr(monster, field_name):
        print(f"[Error] Field '{field_name}' does not exist in the monster definition.")
        return False

    current_value = getattr(monster, field_name)

    try:
        if isinstance(current_value, int):
            value = int(value_str)

        elif isinstance(current_value, float):
            value = float(value_str)

        elif isinstance(current_value, str):
            value = value_str

        else:
            print(f"[Error] Field type '{type(current_value)}' is not supported.")
            return False
        
    except ValueError:
        print(f"[Error] Invalid value '{value_str}' for field '{field_name}'.")
        return False

    setattr(monster, field_name, value)
    print(f"Field '{field_name}' for Monster ID {monster_id} successfully changed to: {value}")
    return True


def save_monster_params(monster_params_obj, path_out="btl_monster_param_10_modified.bin"):
    original_content = bytearray(read_file(Path(".", "btl_monster_param_10.bin")))
    byte_ptr = BytePtr()
    byte_ptr.set_data(original_content)

    header = MonsterParamsFileHandler.BTL_MONSTER_PARAM_HEADER(byte_ptr)
    header.load()
    byte_ptr.pos = header.monster_param_offset

    for param in monster_params_obj.monster_params:
        param.ptr = byte_ptr
        param.save()

    with open(path_out, "wb") as f:
        f.write(original_content)

    print(f"File successfully saved: {path_out}")


def main():
    parser = argparse.ArgumentParser(description="Monster Parameter Modifier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser("set", help="Set a monster parameter")
    set_parser.add_argument("monster_id", type=int, help="Monster ID (ingame ID)")
    set_parser.add_argument("field", type=str, help="Fieldname (z.B. power, agility, name)")
    set_parser.add_argument("value", help="New Value")

    args = parser.parse_args()

    monster_params = MonsterParams(Path("."))
    monster_params.load()

    if args.command == "set":
        success = set_monster_param(monster_params, args.monster_id, args.field, args.value)
        if success:
            save_monster_params(monster_params)


if __name__ == "__main__":
    main()
