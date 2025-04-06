import argparse

from pathlib import Path

from BinaryUtils import BytePtr
from ScriptInterpreter import SPI_STACK, SPI_TAG_PARAM, ScriptInterpreter
from Utils import fix_umlaute, read_file


class Items:
    def __init__(self, iso_dir, lang_id):
        self.iso_dir = iso_dir
        self.lang_id = lang_id

        self.items = {}
        self.SPI_TAG_LOAD_ITEM_NAME = SPI_TAG_PARAM("NAME", self.SI_ITEM_NAME)


    def SI_ITEM_NAME(self, SPI_STACK: SPI_STACK, n):
        item_id = SPI_STACK.get_stack_int()
        SPI_STACK.forward()

        item_name = fix_umlaute(SPI_STACK.get_stack_string())
        SPI_STACK.forward()

        self.items[item_id] = item_name

        
    def load(self):
        filename = Path(self.iso_dir, "bin_ext", f"itemstr1_{self.lang_id}.lst")
        file_content = read_file(filename)

        file_size = len(file_content)
        byte_ptr = BytePtr()
        byte_ptr.set_data(file_content)

        interpreter = ScriptInterpreter()
        interpreter.set_tag([self.SPI_TAG_LOAD_ITEM_NAME])
        interpreter.set_script(byte_ptr, file_size)
        interpreter.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Items")
    subparsers = parser.add_subparsers(dest="command", required=True)
    dump_parser = subparsers.add_parser("list", help="list items")

    dump_parser.add_argument("data_dir", type=str, help="Data directory")
    dump_parser.add_argument("lang_id", type=int, help="Language ID")
    
    args = parser.parse_args()
    items = Items(Path(args.data_dir), args.lang_id)
    items.load()

    for item_id, item_name in items.items.items():
        print(f"Item ID: {item_id}, Item Name: {item_name}")