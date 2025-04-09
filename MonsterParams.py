import argparse

from pathlib import Path

from Actions import Actions
from Utils import fix_umlaute, read_file, SafeEnum
from BinaryUtils import BytePtr
from ObjDump import dump_obj
from ScriptInterpreter import SPI_TAG_PARAM, SPI_STACK, ScriptInterpreter
from IDMappedTextFileParser import parse_id_mapped_text_file
from VersionInfo import VersionInfo
from Items import Items


class TRIPLE_ACTION(SafeEnum):
	T1 = 0
	T1_2 = 1
	T2 = 2
	T3 = 3
	ROT_1_2 = 4
	ROT_1_3 = 5
	ROT_2_1 = 6
	ROT_3_1 = 7
	

class MonsterParamsFileHandler:
    def __init__(self, data_dir):
        self.data_dir = data_dir

        self.monster_params = []


    class BTL_MONSTER_PARAM_HEADER:
        def __init__(self, byte_ptr: BytePtr):
            self.ptr = byte_ptr
        

        def load(self):
            self.version_info = VersionInfo(self.ptr)
            self.version_info.load()

            self.version = self.ptr.get_string(32)
            self.monster_num = self.ptr.get_int32()
            self.monster_param_offset = self.ptr.get_int32()
            self.table_num = self.ptr.get_int32()
            self.table_offset = self.ptr.get_int32()


    class BTL_MONSTER_PARAM:
        def __init__(self, byte_ptr: BytePtr):
            self.ptr = byte_ptr

            self.exclude_dump = ("dummy1", "dummy2", "dummy3", "dummy4", "zero_padding1", "zero_padding2")

            self._fields = [
                ("name", "string", 32),
                ("monster_id", "uint16"),
                ("book_series_id", "byte"),
                ("dummy1", "bytes_array", 1),
                ("series", "uint16"),
                ("level", "byte"),
                ("dummy2", "bytes_array", 1),
                ("book_id", "uint16"),
                ("dummy3", "bytes_array", 2),
                ("maxHP", "int32"),
                ("maxMP", "int32"),
                ("agility", "int32"),
                ("power", "int32"),
                ("defense", "int32"),
                ("exp", "int32"),
                ("gold", "int32"),
                ("a_item", "uint16_array", 2),
                ("a_item_probability", "bytes_array", 2),
                ("absolute_omiyage", "byte"),
                ("a_spell_defense", "bytes_array", 7),
                ("a_tension_defense", "byte"),
                ("init_status", "byte"),
                ("init_status_rate", "byte"),
                ("zero_padding1", "bytes_array", 7),
                ("intelligence", "byte"),
                ("pattern", "byte"),
                ("a_action", "uint16_array", 6),
                ("a_group", "bytes_array", 6),
                ("triple_action", "byte"),
                ("concentrated_atack", "byte"),
                ("recovery", "byte"),
                ("mikawashi", "byte"),
                ("frighten", "byte"),
                ("dummy4", "bytes_array", 1),
                ("unique_id", "uint16"),
                ("zero_padding2", "bytes_array", 4)
            ]

        def load(self):
            for name, typ, *args in self._fields:
                setattr(self, name, getattr(self.ptr, f"get_{typ}")(*args))


        def save(self):
            for name, typ, *args in self._fields:
                value = getattr(self, name)
                getattr(self.ptr, f"set_{typ}")(value, *args)


    class BATTLE_TABLE:
        def __init__(self, byte_ptr: BytePtr):
            self.ptr = byte_ptr


        class RECOVER_HP:
            def __init__(self, byte_ptr: BytePtr):
                self.ptr = byte_ptr

                
            def load(self):
                self.min = self.ptr.get_uint16()
                self.max = self.ptr.get_uint16()

                return self


        class THREAT_RATE_RESULT:
            def __init__(self, byte_ptr: BytePtr):
                self.ptr = byte_ptr

                
            def load(self):
                self.runaway = self.ptr.get_byte()
                self.surprised = self.ptr.get_byte()
                self.attack = self.ptr.get_byte()
                self.no_reaction = self.ptr.get_byte()

                return self


        class THREAT_RATE:
            def __init__(self, byte_ptr: BytePtr):
                self.ptr = byte_ptr

                
            def load(self):
                self.level = self.ptr.get_uint16()
                self.result = [MonsterParamsFileHandler.BATTLE_TABLE.THREAT_RATE_RESULT(self.ptr).load() for _ in range(2)]

                return self


        class RECOVER_STAT_RATE:
            def __init__(self, byte_ptr: BytePtr):
                self.ptr = byte_ptr

                
            def load(self):
                self.player = self.ptr.get_byte()
                self.monster = self.ptr.get_byte()

                return self


        class LINE_GRAPH:
            def __init__(self, byte_ptr: BytePtr):
                self.ptr = byte_ptr

                
            def load(self):
                self.param = self.ptr.get_uint16()
                self.rate = self.ptr.get_uint16()

                return self

        
        def load(self):
            self.a_item_rate = [self.ptr.get_uint16() for _ in range(8)]
            self.a_recover_hp = [MonsterParamsFileHandler.BATTLE_TABLE.RECOVER_HP(self.ptr).load() for _ in range(4)]
            self.a_threat_rate = [MonsterParamsFileHandler.BATTLE_TABLE.THREAT_RATE(self.ptr).load() for _ in range(16)]
            self.a_step_out_rate = self.ptr.get_uint16_array(5)
            self.a_action_pattern_rate = [
                self.ptr.get_bytes_array(6)
                for _ in range(4)
            ]

            self.a_recover_stat_rate = [
                [self.RECOVER_STAT_RATE(self.ptr).load() for _ in range(4)]  # Spalten
                for _ in range(3)                                            # Zeilen
            ]

            self.a_target_player_rate = [
                self.ptr.get_bytes_array(5)
                for _ in range(5)
            ]

            self.ptr.skip(1)

            self.a_step_out_line_graph = [self.LINE_GRAPH(self.ptr).load() for _ in range(11)]
            self.a_kabau_line_graph = [self.LINE_GRAPH(self.ptr).load() for _ in range(11)]
            self.a_mitoreru_line_graph = [self.LINE_GRAPH(self.ptr).load() for _ in range(11)]

            return self
        

    def load(self):
        byte_ptr = BytePtr()

        file_content = read_file(Path(self.data_dir, "bin_ext", "btl_monster_param_10.bin"))

        byte_ptr.set_data(file_content)

        header = self.BTL_MONSTER_PARAM_HEADER(byte_ptr)
        header.load()

        byte_ptr.pos = header.monster_param_offset
        for i in range(header.monster_num):
            monster_param = self.BTL_MONSTER_PARAM(byte_ptr)
            monster_param.load()
            self.monster_params.append(monster_param)

        self.monster_action_table = [self.BATTLE_TABLE(byte_ptr).load() for _ in range(header.table_num)]


class MonsterParamsPostProcessor:
    def __init__(self, data_dir: str, lang_id: int, monster_params: list[MonsterParamsFileHandler.BTL_MONSTER_PARAM], monster_action_table):
        self.data_dir = data_dir
        self.lang_id = lang_id
        self.monster_params = monster_params

        self.monster_action_table = monster_action_table

        self.SPI_TAG_LOAD_MONSTER_NAME = SPI_TAG_PARAM("MN", self.SI_MONS_NAME)
            

    def monster_id_to_unit_id(self, monster_id: int):
        for param in self.monster_params:
            if param.monster_id == monster_id:
                return param.unique_id
            
        return None
    
    
    def get_monster_param(self, unique_id: int):
        for param in self.monster_params:
            if param.unique_id == unique_id:
                return param

        return None
    

    def SI_MONS_NAME(self, SPI_STACK: SPI_STACK, n):
        unique_id = SPI_STACK.get_stack_int()
        SPI_STACK.forward()

        monster_name = fix_umlaute(SPI_STACK.get_stack_string())
        SPI_STACK.forward()

        num = SPI_STACK.get_stack_int()
        SPI_STACK.forward()

        monster_param = self.get_monster_param(unique_id)
        if monster_param is not None:
            monster_param.name_processed = monster_name


    def process_monster_name(self):
        filename = Path(self.data_dir, "bin_ext", f"monster_name_{self.lang_id}.txt")
        file_content = read_file(filename)

        file_size = len(file_content)
        byte_ptr = BytePtr()
        byte_ptr.set_data(file_content)

        for monster_param in self.monster_params:
            monster_param.name_processed = ""

        interpreter = ScriptInterpreter()
        interpreter.set_tag([self.SPI_TAG_LOAD_MONSTER_NAME])
        interpreter.set_script(byte_ptr, file_size)
        interpreter.run()

        for monster_param in self.monster_params:
            if monster_param.name_processed == "":
                monster_param.name_processed = "(Deleted)"

    
    def process_monster_actions(self):
        actions = Actions(self.data_dir, self.lang_id)
        actions.load()

        for monster_param in self.monster_params:
            a_action_list = list(monster_param.a_action)
            for i, action in enumerate(a_action_list):
                if action in actions.actions:
                    a_action_list[i] = actions.actions[action]

            monster_param.a_action_processed = tuple(a_action_list)


    def process_monster_items(self):
        items = Items(self.data_dir, self.lang_id)
        items.load()
        for monster_param in self.monster_params:
            a_item_list = list(monster_param.a_item)
            for i, item_id in enumerate(monster_param.a_item):
                a_item_list[i] = items.items[item_id]

            monster_param.a_item_processed = tuple(a_item_list)


    def calculate_item_drop_chance(self, probability_index, a_item_rate, adjust_rate):
        drop_rate = a_item_rate[probability_index]
        if drop_rate <= 0 or drop_rate >= 4096:
            return 0.0

        denominator = drop_rate * 100 / adjust_rate
        if denominator < 1:
            denominator = 1 

        probability = 1.0 / denominator
        return probability 
    

    def process_item_drop_rate(self):
        for monster_param in self.monster_params:
            monster_param.a_item_probability_processed = []
            for i in range(2):
                probability_index = monster_param.a_item_probability[i]
                monster_param.a_item_probability_processed.append(self.calculate_item_drop_chance(probability_index, self.monster_action_table[0].a_item_rate, 100))


    def process_additional_is_wander(self):
        file_content = read_file(Path(self.data_dir, "bin_ext", "wander_mons_name_1.txt")).decode("shift-jis")
        data = parse_id_mapped_text_file(file_content)
        for monster_param in self.monster_params:
            if monster_param.unique_id in data:
                monster_param.is_wander_additional = True

            else:
                monster_param.is_wander_additional = False


    def process_enums(self):
        for monster_param in self.monster_params:
            monster_param.triple_action_enum = TRIPLE_ACTION(monster_param.triple_action)


class MonsterParams:
    def __init__(self, data_dir, lang_id: int=1):
        self.data_dir = data_dir
        self.lang_id = lang_id

        self.monster_params = None
    

    get_monster_param = MonsterParamsPostProcessor.get_monster_param
    monster_id_to_unit_id = MonsterParamsPostProcessor.monster_id_to_unit_id

    def load(self):
        monster_params_file_handler = MonsterParamsFileHandler(self.data_dir)
        monster_params_file_handler.load()

        monster_params_post_processor = MonsterParamsPostProcessor(self.data_dir, self.lang_id, monster_params_file_handler.monster_params, monster_params_file_handler.monster_action_table)

        monster_params_post_processor.process_monster_name()
        monster_params_post_processor.process_monster_actions()
        monster_params_post_processor.process_monster_items()
        monster_params_post_processor.process_item_drop_rate()
        monster_params_post_processor.process_additional_is_wander()
        monster_params_post_processor.process_enums()

        self.monster_params = monster_params_post_processor.monster_params
        self._monster_action_table = monster_params_file_handler.monster_action_table


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monster Parameter Dumper")
    subparsers = parser.add_subparsers(dest="command", required=True)
    dump_parser = subparsers.add_parser("dump", help="Dump monster parameters")

    dump_parser.add_argument("data_dir", type=str, help="Data directory")
    dump_parser.add_argument("lang_id", type=int, help="Language ID")
    
    args = parser.parse_args()

    monster_params = MonsterParams(Path(args.data_dir), args.lang_id)
    monster_params.load()
    
    with open("monster_params.json", "w", encoding="utf-8") as f:
        f.write(
            dump_obj(
                monster_params.monster_params,
                desired_order = ["name", "name_processed", "monster_id", "is_wander_additional", "book_series_id", "series", "level", "book_id",
                                "maxHP", "maxMP", "agility", "power", "defense", "exp", "gold",
                                "a_item", "a_item_processed", "a_item_probability", "a_item_probability_processed", "absolute_omiyage", "a_spell_defense",
                                "a_tension_defense", "init_status", "init_status_rate", "intelligence",
                                "pattern", "a_action", "a_action_processed", "a_group", "triple_action", "triple_action_enum", "concentrated_atack",
                                "recovery", "mikawashi", "frighten", "unique_id"]
            )
        )

    with open("monster_action_table.json", "w", encoding="utf-8") as f:
        f.write(dump_obj(monster_params._monster_action_table))