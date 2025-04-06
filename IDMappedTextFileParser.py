from Utils import fix_umlaute


def parse_id_mapped_text_file(file_content: str) -> dict:
    mapping = {}

    last_id = None
    
    for line in file_content.splitlines():
        line = line.strip()
        if line.startswith("@"):
            last_id = int(line.split("//")[0][1:])
            mapping[last_id] = []

        else:
            if line != "":
                mapping[last_id].append(fix_umlaute(line))

    return mapping