import argparse

from pathlib import Path

from IDMappedTextFileParser import parse_id_mapped_text_file
from Utils import read_file


class Actions:
    def __init__(self, data_dir: str, lang_id: int):
        self.data_dir = data_dir
        self.lang_id = lang_id

        self.actions = []


    def load(self):
        filename = Path(self.data_dir, "bin_ext", f"action_name_{self.lang_id}.txt")
        file_content = read_file(filename)
        self.actions = parse_id_mapped_text_file(file_content.decode("utf-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Actions")
    subparsers = parser.add_subparsers(dest="command", required=True)
    dump_parser = subparsers.add_parser("list", help="list actions")

    dump_parser.add_argument("data_dir", type=str, help="Data directory")
    dump_parser.add_argument("lang_id", type=int, help="Language ID")
    
    args = parser.parse_args()
    actions = Actions(Path(args.data_dir), args.lang_id)
    actions.load()

    for action_id, action_name in actions.actions.items():
        print(f"Action ID: {action_id}, Action Name: {action_name[0]}")
    