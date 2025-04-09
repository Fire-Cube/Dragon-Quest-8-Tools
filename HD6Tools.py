import argparse
import os

from pathlib import Path

from BinaryUtils import BytePtr
from Utils import read_file


def uint16_to_int(bytes_array: bytes) -> int:
    return (bytes_array[0] & 0xFF) | ((bytes_array[1] & 0xFF) << 8)


def uint24_to_int(bytes_array: bytes) -> int:
    return (bytes_array[0] & 0xFF) | ((bytes_array[1] & 0xFF) << 8) | ((bytes_array[2] & 0xFF) << 16)


def get_name_chunk_data_offset_array(name_chunk_data: bytes) -> list:
    offsets = [0]
    for i, byte in enumerate(name_chunk_data):
        if byte == 0:
            offsets.append(i + 1)

    return offsets


def align(value: int, alignment: int) -> int:
    return ((value + alignment - 1) // alignment) * alignment


class HD6Header:
    def __init__(self, ptr: BytePtr):
        self.ptr = ptr


    def load(self):
        magic = self.ptr.get_string(3)
        if not magic == "HD6":
            raise ValueError("Invalid HD6 file format!")
        
        self.ptr.skip(5)
        self.name_chunk_data_size = self.ptr.get_uint32()
        self.ptr.skip(8)
        self.p_filename_table = self.ptr.get_uint32()
        self.filename_table_size = self.ptr.get_uint32()
        self.ptr.skip(8)
        self.file_count = self.ptr.get_uint32() - 1
        self.p_file_entries = self.ptr.get_uint32()
        self.ptr.skip(8)


class HD6Extractor:
    def __init__(self, hd6_path: Path):
        self.hd6_path = hd6_path
        
        self.ptr = BytePtr()
        self.header = None
        self.name_chunk_data = b""
        self.filename_table = b""
        self.file_entries = []


    def load(self):
        hd6_bytes = read_file(self.hd6_path)

        self.ptr.set_data(hd6_bytes)
        self.header = HD6Header(self.ptr)
        self.header.load()

        self.name_chunk_data = self.ptr.get_bytes_array(self.header.name_chunk_data_size)

        position = self.ptr.pos
        if self.header.p_filename_table > position:
            self.ptr.skip(self.header.p_filename_table - position)

        self.filename_table = self.ptr.get_bytes_array(self.header.filename_table_size)

        position = self.ptr.pos
        if self.header.p_file_entries > position:
            self.ptr.skip(self.header.p_file_entries - position)

        for _ in range(self.header.file_count):
            entry = self.ptr.get_bytes_array(8)
            self.file_entries.append(entry)


    def parse_file_entries(self):
        start_offset_array = []
        file_size_array = []
        for entry in self.file_entries:
            ptr_entry = BytePtr()
            ptr_entry.set_data(entry)
            ptr_entry.skip(2)
            bytes_array = ptr_entry.get_bytes_array(3)
            start_offset = (uint24_to_int(bytes_array) & 0xFFFFFC) << 9
            start_offset_array.append(start_offset)

            bytes_array = ptr_entry.get_bytes_array(3)
            file_size = uint24_to_int(bytes_array) << 4
            file_size_array.append(file_size)

        return start_offset_array, file_size_array


    def decode_filenames(self, no_system_delemiters=False):
        offsets = get_name_chunk_data_offset_array(self.name_chunk_data)
        filenames = []

        ptr_file_table = BytePtr()
        ptr_file_table.set_data(self.filename_table)

        for _ in range(self.header.file_count):
            name_bytes = bytearray()
            while True:
                byte = ptr_file_table.get_byte()
                if byte == 0:
                    break

                if byte & 0x80:
                    byte2 = ptr_file_table.get_byte()
                    short_index = uint16_to_int(bytes([byte, byte2]))
                    factor = byte2 + 1
                    final_index = short_index - (factor * 0x80)

                else:
                    final_index = byte

                current_offset = offsets[final_index]
                next_offset = offsets[final_index + 1]
                chunk_size = next_offset - current_offset - 1
                name_bytes.extend(self.name_chunk_data[current_offset:current_offset + chunk_size])

            try:
                decoded = name_bytes.decode("shift_jis")

            except Exception:
                decoded = name_bytes.decode("shift_jis", errors="replace")
            
            if not no_system_delemiters:
                decoded = decoded.replace("\\", os.path.sep)

            filenames.append(decoded)

        return filenames


class Extraction:
    def __init__(self, dat_path: Path, hd6_path: Path, dest_folder_path: Path):
        self.dat_path = dat_path
        self.hd6_path = hd6_path
        self.dest_folder_path = dest_folder_path


    def perform(self) -> bool:
        if not self.dat_path.exists():
            print("[Error] Data file could not be found!")
            return False
        
        if not self.hd6_path.exists():
            print("[Error] HD6 file could not be found!")
            return False
        
        if not self.dest_folder_path.exists():
            print("Destination folder does not exist. Creating it...")
            self.dest_folder_path.mkdir(parents=True, exist_ok=True)

        hd6_extractor = HD6Extractor(self.hd6_path)
        hd6_extractor.load()
        start_offsets, file_sizes = hd6_extractor.parse_file_entries()
        filenames = hd6_extractor.decode_filenames()

        try:
            dat_bytes = read_file(self.dat_path)

        except Exception as exception:
            print("[Error] Could not open DAT file!", exception)
            return False

        dat_byte_ptr = BytePtr()
        dat_byte_ptr.set_data(dat_bytes)

        print("Writing files...")
        for i, filename in enumerate(filenames):
            start_offset = start_offsets[i]
            file_size = file_sizes[i]
            dat_byte_ptr.pos = start_offset
            file_data = dat_byte_ptr.get_bytes_array(file_size)
            dest_file_path = self.dest_folder_path / filename
            dest_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_file_path, "wb") as f:
                f.write(file_data)

            print(f"Written: {dest_file_path}")

        return True


class Replacement:
    def __init__(self, dat_path: Path, hd6_path: Path, target_filename: str, new_file_path: Path):
        self.dat_path = dat_path
        self.hd6_path = hd6_path
        self.target_filename = target_filename
        self.new_file_path = new_file_path

    def perform(self) -> bool:
        if not self.dat_path.exists():
            print("[Error] DAT file not found!")
            return False
        
        if not self.hd6_path.exists():
            print("[Error] HD6 file not found!")
            return False
        
        if not self.new_file_path.exists():
            print("[Error] New file not found!")
            return False
        
        hd6_extractor = HD6Extractor(self.hd6_path)
        hd6_extractor.load()
        start_offsets, file_sizes = hd6_extractor.parse_file_entries()
        filenames = hd6_extractor.decode_filenames()

        try:
            target_index = filenames.index(self.target_filename)

        except ValueError:
            print(f"[Error] Target filename '{self.target_filename}' not found in HD6!")
            return False

        old_offset = start_offsets[target_index]
        old_size = file_sizes[target_index]
        print(f"Replacing file '{self.target_filename}' at offset {old_offset} with size {old_size}")

        try:
            new_data = read_file(self.new_file_path)

        except Exception as exception:
            print("[Error] Error reading new file:", exception)
            return False

        new_size = len(new_data)
        if new_size % 16 != 0:
            padded_size = ((new_size + 15) // 16) * 16
            new_data += b"\x00" * (padded_size - new_size)
            new_size = padded_size

        print(f"New file size (aligned): {new_size}")

        delta = new_size - old_size
        print(f"Size difference (delta): {delta}")

        try:
            dat_bytes = bytearray(read_file(self.dat_path))

        except Exception as exception:
            print("[Error] Error reading DAT file:", exception)
            return False

        if old_offset + old_size > len(dat_bytes):
            print("[Error]  Target file range exceeds DAT file size!")
            return False

        new_dat_bytes = dat_bytes[:old_offset] + new_data + dat_bytes[old_offset+old_size:]
        try:
            with open(self.dat_path, "wb") as f:
                f.write(new_dat_bytes)

        except Exception as exception:
            print("[Error] Error writing DAT file:", exception)
            return False
        
        print("DAT file updated.")

        try:
            hd6_bytes = bytearray(read_file(self.hd6_path))

        except Exception as exception:
            print("[Error] Error reading HD6 file for update:", exception)
            return False

        file_entries_offset = hd6_extractor.header.p_file_entries
        file_count = hd6_extractor.header.file_count

        for i in range(file_count):
            entry_offset = file_entries_offset + i * 8
            entry = bytearray(hd6_bytes[entry_offset:entry_offset + 8])

            stored_offset_val = int.from_bytes(entry[2:5], "little")
            stored_size_val = int.from_bytes(entry[5:8], "little")
            actual_offset = (stored_offset_val & 0xFFFFFC) << 9
            actual_size = stored_size_val << 4

            if i == target_index:
                new_stored_size = (new_size >> 4)
                new_stored_size_bytes = new_stored_size.to_bytes(3, "little")
                hd6_bytes[entry_offset + 5:entry_offset + 8] = new_stored_size_bytes

            elif i > target_index:
                new_actual_offset = actual_offset + delta
                new_stored_offset = (new_actual_offset >> 9) & 0xFFFFFF
                new_stored_offset_bytes = new_stored_offset.to_bytes(3, "little")
                hd6_bytes[entry_offset + 2:entry_offset + 5] = new_stored_offset_bytes

        try:
            with open(self.hd6_path, "wb") as f:
                f.write(hd6_bytes)

        except Exception as exception:
            print("[Error] Error writing HD6 file:", exception)
            return False
        
        print("HD6 file updated.")

        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract, replace or list files in the DAT archive and update the HD6 file accordingly."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract", help="Extract files from DAT using HD6.")
    extract_parser.add_argument("dat_path", type=str, help="Path to the DAT file.")
    extract_parser.add_argument("hd6_path", type=str, help="Path to the HD6 file.")
    extract_parser.add_argument("destination_folder", type=str, help="Destination folder for extracted files.")

    replace_parser = subparsers.add_parser("replace", help="Replace a file in the DAT and update HD6.")
    replace_parser.add_argument("dat_path", type=str, help="Path to the DAT file.")
    replace_parser.add_argument("hd6_path", type=str, help="Path to the HD6 file.")
    replace_parser.add_argument("target_filename", type=str, help="Filename inside HD6/DAT to replace.")
    replace_parser.add_argument("new_file", type=str, help="Path to the new file to insert.")

    list_parser = subparsers.add_parser("list", help="List filenames in the HD6 file.")
    list_parser.add_argument("dat_path", type=str, help="Path to the DAT file.")
    list_parser.add_argument("hd6_path", type=str, help="Path to the HD6 file.")

    args = parser.parse_args()

    if args.command == "extract":
        dat_path = Path(args.dat_path)
        hd6_path = Path(args.hd6_path)
        destination_folder = Path(args.destination_folder)
        extractor = Extraction(dat_path, hd6_path, destination_folder)
        if extractor.perform():
            print("Extraction successful!")

        else:
            print("[Error] Extraction failed!")

    elif args.command == "replace":
        dat_path = Path(args.dat_path)
        hd6_path = Path(args.hd6_path)
        target_filename = args.target_filename
        new_file_path = Path(args.new_file)
        replacer = Replacement(dat_path, hd6_path, target_filename, new_file_path)
        if replacer.perform():
            print("Replacement successful!")

        else:
            print("[Error] Replacement failed!")

    elif args.command == "list":
        dat_path = Path(args.dat_path)
        hd6_path = Path(args.hd6_path)
        extractor = HD6Extractor(hd6_path)
        extractor.load()
        extractor.parse_file_entries()
        filenames = extractor.decode_filenames(no_system_delemiters=True)

        for filename in filenames:
            print(filename)