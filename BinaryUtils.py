import struct


class BytePtr:
    def __init__(self):
        self.byte_data = bytearray()
        self.pos = 0


    def get_remaining_bytes_amount(self) -> int:
        return len(self.byte_data) - self.pos
    

    def skip(self, count: int) -> None:
        self.pos += count


    def set_data(self, data: bytes) -> None:
        self.byte_data = data
        self.pos = 0

    
    def get_int16(self) -> int:
        val = struct.unpack_from("<h", self.byte_data, self.pos)[0]
        self.skip(2)
        return val
    

    def get_uint16(self) -> int:
        val = struct.unpack_from("<H", self.byte_data, self.pos)[0]
        self.skip(2)
        return val


    def set_uint16(self, val: int) -> None:
        struct.pack_into("<H", self.byte_data, self.pos, val)
        self.skip(2)


    def get_uint16_array(self, count: int) -> list[int]:
        val = struct.unpack_from("<" + "H" * count, self.byte_data, self.pos)
        self.skip(2 * count)
        return val
    

    def set_uint16_array(self, val: list[int], count: int) -> None:
        struct.pack_into("<" + "H" * count, self.byte_data, self.pos, *val)
        self.skip(2 * count)


    def get_int32(self) -> int:
        val = struct.unpack_from("<i", self.byte_data, self.pos)[0]
        self.skip(4)
        return val
    

    def set_int32(self, val: int) -> None:
        struct.pack_into("<i", self.byte_data, self.pos, val)
        self.skip(4)
    

    def get_uint32(self) -> int:
        val = struct.unpack_from("<I", self.byte_data, self.pos)[0]
        self.skip(4)
        return val
    

    def get_uint32_array(self, count: int) -> list[int]:
        val = struct.unpack_from("<" + "I" * count, self.byte_data, self.pos)
        self.skip(4 * count)
        return val
    

    def get_float(self) -> float:
        val = struct.unpack_from("<f", self.byte_data, self.pos)[0]
        self.skip(4)
        return val
    
    
    def get_byte(self) -> bytes:
        val = self.byte_data[self.pos]
        self.skip(1)
        return val
    

    def set_byte(self, val: bytes) -> None:
        self.byte_data[self.pos] = val
        self.skip(1)


    def get_bytes_array(self, count: int) -> bytes:
        val = self.byte_data[self.pos:self.pos + count]
        self.skip(count)
        return val


    def set_bytes_array(self, val: bytes, count: int) -> None:
        self.byte_data[self.pos:self.pos + count] = val
        self.skip(count)


    def get_string(self, count: int, utf8=False) -> str:
        num = count
        for i in range(count):
            if self.byte_data[self.pos + i] == 0:
                num = i
                break
        
        data = self.byte_data[self.pos:self.pos + num]
        if utf8:
            val = data.decode("utf-8")

        else:
            val = data.decode("shift-jis", errors='replace')

        self.skip(count)
        return val
    

    def set_string(self, val: str, length: int, utf8=False) -> None:
        if utf8:
            data = val.encode("utf-8", errors="replace")

        else:
            data = val.encode("shift-jis", errors="replace")
        
        if len(data) < length:
            data += b"\x00" * (length - len(data))

        else:
            data = data[:length]

        self.byte_data[self.pos:self.pos + length] = data
        self.skip(length)
