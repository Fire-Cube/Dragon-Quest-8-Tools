import argparse

from pathlib import Path
from typing import Callable

from BinaryUtils import BytePtr
from Utils import read_file

KNOWN_FILE_EXTENSIONS = (
    ("pak", "general package"),
    ("mpk", "map package"),
    ("pcp", "map piece package"),
    ("ipk", "information data package"),
    ("nav", "navigation data package"),
    ("sky", "sky data package"),
    ("snd", "sound data package"),
    ("pac", "contains snd files"),
    ("chr", "?"),
)

class FileHeader:
    def __init__(self, byte_ptr: BytePtr):
        self.ptr = byte_ptr


    def load(self):
        self.file_name = self.ptr.get_string(64)
        self.relative_file_offset = self.ptr.get_int32()
        self.file_size = self.ptr.get_int32()
        self.next_header_offset = self.ptr.get_int32()
        self.version = self.ptr.get_int32()


class FileData:
    def __init__(self, byte_ptr: BytePtr, file_size: int):
        self.ptr = byte_ptr
        self.file_size = file_size


    def load(self) -> bytes:
        return self.ptr.get_bytes_array(self.file_size)


def process_pak_file(pak_path: str, processor: Callable[[BytePtr, FileHeader], None]) -> None:
    pak_path = Path(pak_path)
    if not pak_path.exists() or not pak_path.is_file():
        print(f"File not found: {pak_path}")
        return
    
    if pak_path.suffix[1:] not in [extension for extension, _ in KNOWN_FILE_EXTENSIONS]:
        print(f"Unknown file extension: {pak_path.suffix}")
        return
    
    file_content = read_file(pak_path)
    byte_ptr = BytePtr()
    byte_ptr.set_data(file_content)
    
    while True:
        start_pos = byte_ptr.pos

        file_header = FileHeader(byte_ptr)
        file_header.load()

        if file_header.file_name == "" or file_header.next_header_offset <= 0:
            break
        
        byte_ptr.set_pos(start_pos + file_header.relative_file_offset)
        processor(byte_ptr, file_header)

        byte_ptr.set_pos(start_pos + file_header.next_header_offset)

        if byte_ptr.get_remaining_bytes_amount() < 80:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract or list files in the PAK archive."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract", help="Extract files from PAK.")
    extract_parser.add_argument("pak_path", type=str, help="Path to the PAK file.")
    extract_parser.add_argument("destination_folder", type=str, help="Destination folder for extracted files.")

    replace_parser = subparsers.add_parser("replace", help="Replace a file in the PAK.")
    replace_parser.add_argument("pak_path", type=str, help="Path to the PAK file.")

    replace_parser.add_argument("target_filename", type=str, help="Filename inside PAK to replace.")
    replace_parser.add_argument("new_file", type=str, help="Path to the new file to insert.")

    list_parser = subparsers.add_parser("list", help="List filenames in the HD6 file.")
    list_parser.add_argument("pak_path", type=str, help="Path to the PAK file.")

    args = parser.parse_args()

    if args.command == "extract":
        target_path = Path(args.destination_folder)
        if not Path(target_path).exists():
            target_path.mkdir(parents=True)

        def extract_file(byte_ptr: BytePtr, file_header: FileHeader):
            file_data = FileData(byte_ptr, file_header.file_size)
            dest_file_path = Path(target_path, file_header.file_name)
            with open(dest_file_path, "wb") as file:
                file.write(file_data.load())

            print("Written:", dest_file_path, file_header.file_size, "bytes")


        process_pak_file(args.pak_path, extract_file)


    elif args.command == "replace":
        print("Not implemented yet")

    elif args.command == "list":
        def list_file(byte_ptr: BytePtr, file_header: FileHeader):
            print(file_header.file_name, file_header.file_size, "bytes")


        process_pak_file(args.pak_path, list_file)