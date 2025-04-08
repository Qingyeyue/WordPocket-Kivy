import os
from data import Data

class Filter:
    @staticmethod
    def create_filtered_lexicon_from_existing(lexicon_name, scheme, new_lexicon_name):
        from lexicon import Lexicon  # 延迟导入避免循环引用

        lexicon = Lexicon()
        entries = lexicon.get_lexicon_entries(lexicon_name)

        # 筛选符合方案的条目
        filtered_entries = Data.filter_entries(entries, scheme)

        # 删除已存在的目标词库（如果有）
        if new_lexicon_name in lexicon.get_lexicon_list():
            lexicon.delete_lexicon(new_lexicon_name)

        # 保存新词库
        lexicon.save_lexicon(new_lexicon_name, filtered_entries)
        return filtered_entries
