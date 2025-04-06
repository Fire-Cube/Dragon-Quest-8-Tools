from BinaryUtils import BytePtr


class VersionInfo:
    def __init__(self, byte_ptr: BytePtr):
        self.ptr = byte_ptr
    

    def load(self):
        self.version = self.ptr.get_string(8)
        self.created_date_time = self.ptr.get_string(20)
        self.ptr.pos += 4