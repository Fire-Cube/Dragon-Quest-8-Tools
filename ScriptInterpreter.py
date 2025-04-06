from BinaryUtils import BytePtr
from typing import Optional

class SPI_TAG_PARAM:
    def __init__(self, tag: str, func=None, func2=None):
        self.tag = tag
        self.func = func
        self.func2 = func2


class SPI_TAG_PARAM2:
    def __init__(self, tag: str, func2):
        self.tag = tag
        self.func2 = func2


class SPI_STACK:
    def __init__(self):
        self.datas = []
        self.pos = 0


    def init(self):
        self.datas = []
        self.pos = 0


    def clear(self):
        self.datas = []
        self.pos = 0


    def push(self, value: str):
        self.datas.append(value)


    @property
    def count(self):
        return len(self.datas)


    def s(self) -> Optional[str]:
        if self.pos < len(self.datas):
            return self.datas[self.pos]
        
        return None
    

    def get_stack_int(self) -> int:
        try:
            val = int(self.s())

        except:
            val = 0

        return val
    

    def get_stack_string(self) -> str:
        return self.s()
    

    def forward(self):
        self.pos += 1
    

class spiFuncParam:
    def __init__(self, param):
        self.param = param
        self.m_ResumeFlag = False


class ScriptInterpreter:
    def __init__(self):
        self.string_buffer = ""
        self.tag_table = []
        self.tag_call_param = None


    def set_tag(self, tags):
        """
        Sets the tag table. tags can either be a list of SPI_TAG_PARAM or SPI_TAG_PARAM2.
        """
        # If the elements have a "func" attribute, we use them directly
        if all(hasattr(tag, "func") for tag in tags):
            self.tag_table = tags

        else:
            # Otherwise, we convert SPI_TAG_PARAM2 to SPI_TAG_PARAM
            self.tag_table = [SPI_TAG_PARAM(tag.tag, func2=tag.func2) for tag in tags]


    def set_tag_with_param(self, tags, call_param):
        """
        Sets the tag table from a list of SPI_TAG_PARAM2 and stores
        the additional parameter.
        """
        self.tag_table = [SPI_TAG_PARAM(tag.tag, func2=tag.func2) for tag in tags]
        self.tag_call_param = call_param


    def set_script(self, script, size=None):
        """
        Sets the script to be interpreted. The script can be a BytePtr, bytes, or string.
        When using BytePtr or bytes, the size must be provided.
        """
        if isinstance(script, BytePtr):
            if size is None:
                raise ValueError("Size must be provided for BytePtr")
            
            self.string_buffer = script.get_string(size)

        elif isinstance(script, bytes):
            bp = BytePtr(script)
            if size is None:
                raise ValueError("Size must be specified for bytes")
            
            self.string_buffer = bp.get_string(size)

        elif isinstance(script, str):
            self.string_buffer = script

        else:
            raise ValueError("Unsupported script type")


    def run(self):
        """
        Parses and executes the script.
        """
        stack = SPI_STACK()
        stack.init()
        i = 0
        buffer_length = len(self.string_buffer)
        while i < buffer_length:
            current_character = self.string_buffer[i]
            # Skip whitespace, tabs, and comments
            while True:
                if current_character in ["\t", " "]:
                    i += 1
                    if i < buffer_length:
                        current_character = self.string_buffer[i]
                        continue

                    else:
                        return
                    
                elif current_character == "/":
                    if i + 1 < buffer_length and self.string_buffer[i+1] == "*":
                        end_comment = self.string_buffer.find("*/", i + 2)
                        if end_comment < 0:
                            return
                        
                        i = end_comment + 2
                        if i < buffer_length:
                            current_character = self.string_buffer[i]
                            continue

                        else:
                            return
                        
                    break

                else:
                    break

            # Check if it's a tag (A-Z or "_")
            if ("A" <= current_character <= "Z") or current_character == "_":
                num = i
                # Read the tag (only A-Z, 0-9, _ allowed)
                while i < buffer_length:
                    current_character = self.string_buffer[i]
                    if not (("A" <= current_character <= "Z") or ("0" <= current_character <= "9") or (current_character == "_")):
                        break

                    i += 1
                

                token = self.string_buffer[num:i]
                # Compare the read tag with the tag table
                for tag_param in self.tag_table:
                    if len(token) == len(tag_param.tag) and token == tag_param.tag:
                        stack.clear()
                        num3 = i
                        # Argument parsing: process any parameters following the tag.
                        while i < buffer_length:
                            current_arg_character = self.string_buffer[i]
                            if current_arg_character == '"':
                                num3 = i + 1
                                quoted_string, i = self.get_quotation_string(i)
                                self.push_stack(stack, quoted_string, False)
                                i += 1  # skip the closing quotation mark
                                if i < buffer_length:
                                    if self.string_buffer[i] == ",":
                                        i += 1
                                        num3 = i
                                        continue

                                    elif self.string_buffer[i] == ";":
                                        i += 1
                                        break

                                    else:
                                        num3 = i
                                        continue

                                else:
                                    break

                            elif current_arg_character == ",":
                                arg = self.string_buffer[num3:i].strip()
                                self.push_stack(stack, arg, True)
                                i += 1
                                num3 = i
                                continue

                            elif current_arg_character == ";":
                                arg = self.string_buffer[num3:i].strip()
                                self.push_stack(stack, arg, True)
                                i += 1
                                break

                            elif current_arg_character in ["\n", "/"]:
                                break

                            else:
                                i += 1
                                continue

                        # Call the corresponding callback function
                        if tag_param.func is not None:
                            tag_param.func(stack, stack.count)

                        elif tag_param.func2 is not None:
                            tag_param.func2(stack, stack.count, spiFuncParam(self.tag_call_param))

                        else:
                            print(f"ScriptInterpreter: Warning: No handler defined for tag \"{tag_param.tag}\".")
                        
            if i >= buffer_length:
                break

            # Go to the next line
            newline_index = self.string_buffer.find("\n", i)
            if newline_index < 0:
                break

            i = newline_index + 1


    def push_stack(self, stack, s, value):
        """
        Inserts a value into the stack.
        """
        stack.push(s)


    def get_quotation_string(self, pos):
        """
        Extracts a string enclosed in double quotes from the string buffer.
        'pos' points to the opening quotation mark.
        """
        start = pos + 1
        while True:
            pos = self.string_buffer.find('"', pos + 1)
            if pos == -1:
                # No closing quotation mark found – return the rest
                return self.string_buffer[start:], pos
            
            # If the double quote is not escaped, it is the closing one
            if self.string_buffer[pos - 1] != "\\":
                break

        return self.string_buffer[start:pos], pos


    @staticmethod
    def analysis(byte_ptr, size, spi_tags):
        """
        Performs the analysis using a BytePtr as input.
        """
        interpreter = ScriptInterpreter()
        interpreter.set_tag(spi_tags)
        interpreter.set_script(byte_ptr, size)
        interpreter.run()


    @staticmethod
    def analysis_text(text, spi_tags):
        """
        Performs analysis using a text input (string).
        """
        interpreter = ScriptInterpreter()
        interpreter.set_tag(spi_tags)
        interpreter.set_script(text)
        interpreter.run()
