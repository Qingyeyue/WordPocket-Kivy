# core/data.py
import json
import os
import re
# 不再需要从这里导入 Lexicon，因为它会被传递进来
# from core.lexicon import Lexicon

class Data:
    # 修改 __init__ 以接收 Lexicon 实例
    def __init__(self, lexicon_instance):
        """
        Initializes the Data handler with a shared Lexicon instance.

        Args:
            lexicon_instance: The shared instance of the Lexicon class.
        """
        # --- 存储共享的 Lexicon 实例 ---
        self.lexicon = lexicon_instance
        # --- 不再需要 self.lexicon = Lexicon(...) ---
        # --- 也不再需要 self.lexicon_dir, self.default_lexicon, self.lexicon_path ---
        # 因为这些路径管理现在由共享的 lexicon_instance 负责

    def search_word(self, word):
        """
        Searches for a word in the defaults list managed by the shared Lexicon instance.
        """
        # --- 直接使用共享实例的 defaults 列表 ---
        if not self.lexicon or not self.lexicon.defaults:
             print("错误: Data.search_word 无法访问 defaults 数据。")
             return None # 或者返回空列表 []

        lexicon_data = self.lexicon.defaults # 获取共享的列表
        results = []

        # 判断输入的是中文还是英文
        is_chinese = bool(re.search(r'[\u4e00-\u9fff]', word)) # 使用 bool() 更明确

        # 转换为小写 (仅对英文有效)
        word_lower = word.lower()

        for entry in lexicon_data:
            # 确保条目是字典并且包含所需键
            if isinstance(entry, dict) and 'chinese' in entry and 'english' in entry:
                chinese = entry['chinese']
                # 对比前也确保英文是字符串
                english_val = entry.get('english', '')
                english_lower = english_val.lower() if isinstance(english_val, str) else ''

                match = False
                if is_chinese:
                    # 中文使用 'in' 进行部分匹配
                    if isinstance(chinese, str) and word in chinese:
                        match = True
                else:
                    # 英文也使用 'in' 进行部分匹配（如果需要部分匹配）
                    # 如果只需要从头开始匹配，用 startswith: if english_lower.startswith(word_lower):
                    if word_lower in english_lower:
                        match = True

                if match:
                    results.append(entry)

        # 如果需要区分精确和部分匹配（基于完整字符串相等）
        exact_matches = []
        partial_matches = []
        for entry in results:
             # 确保比较前类型正确
             entry_chinese = entry.get('chinese', '')
             entry_english_val = entry.get('english', '')
             entry_english_lower = entry_english_val.lower() if isinstance(entry_english_val, str) else ''

             is_exact = False
             if is_chinese:
                 if entry_chinese == word:
                     is_exact = True
             else:
                 if entry_english_lower == word_lower:
                     is_exact = True

             if is_exact:
                 exact_matches.append(entry)
             else:
                 partial_matches.append(entry)


        # 总是返回列表，即使是空列表
        return exact_matches + partial_matches


    @staticmethod
    def get_sort_options():
        # 这个方法是静态的，不需要修改
        return [
            ('按字母正序', 'alphabetical', False), # 修改：正序 reverse=False
            ('按字母逆序', 'alphabetical', True), # 修改：逆序 reverse=True
            ('按查询次数正序', 'inquiry', False),
            ('按查询次数逆序', 'inquiry', True),
            ('按记忆次数正序', 'memory', False),
            ('按记忆次数逆序', 'memory', True),
            ('按错误次数正序', 'mistake', False),
            ('按错误次数逆序', 'mistake', True),
        ]

    @staticmethod
    def sort_entries(entries, sort_by, reverse=False):
        # 这个方法是静态的，逻辑看起来没问题，但注意 alphabetical 可能需要区分中英文
        # 目前按中文排序
        if sort_by == 'alphabetical':
            # 考虑对英文排序: key=lambda x: x.get('english', '').lower()
            # 或者提供中/英文排序选项
            return sorted(entries, key=lambda x: x.get('chinese', ''), reverse=reverse)
        elif sort_by == 'inquiry':
            # 使用 .get(key, default) 来处理可能不存在的键
            return sorted(entries, key=lambda x: x.get('inquiry', 0), reverse=reverse)
        elif sort_by == 'memory':
            return sorted(entries, key=lambda x: x.get('memory', 0), reverse=reverse)
        elif sort_by == 'mistake':
            return sorted(entries, key=lambda x: x.get('mistake', 0), reverse=reverse)
        # 如果 sort_by 无效，返回原列表
        return entries

    @staticmethod
    def filter_entries(entries, scheme):
        # 这个方法是静态的，逻辑看起来没问题，注意 .get 的使用
        if scheme == 'new':
            return [
                entry for entry in entries
                if entry.get('memory', 0) == 0
            ]
        elif scheme == 'consolidate':
            # 巩固：记过(>0)，但还没完全掌握(<6?)，并且错过(>0)
            return [
                entry for entry in entries
                if 0 < entry.get('memory', 0) < 6 and entry.get('mistake', 0) > 0
            ]
        elif scheme == 'review':
            # 复习：记了很多次(>5?)，但错误率仍然较高 (错误 > 记忆次数 / 3 ?)
            # 注意：如果 memory 是 0， division by zero error.
            return [
                entry for entry in entries
                if entry.get('memory', 0) >= 6 and \
                   entry.get('mistake', 0) > (entry.get('memory', 1) / 3) # 避免除零
            ]
        elif scheme == 'all': # 添加一个 'all' 方案
             return list(entries) # 返回所有条目的副本
        elif scheme == 'other': # 重新定义 'other'，排除上面三种情况
            # memory == 0 (new)
            # 0 < memory < 6 and mistake > 0 (consolidate)
            # memory >= 6 and mistake > (memory / 3) (review)
            new_ids = {id(e) for e in Data.filter_entries(entries, 'new')}
            con_ids = {id(e) for e in Data.filter_entries(entries, 'consolidate')}
            rev_ids = {id(e) for e in Data.filter_entries(entries, 'review')}
            return [
                entry for entry in entries
                if id(entry) not in new_ids and \
                   id(entry) not in con_ids and \
                   id(entry) not in rev_ids
            ]
        else: # 如果方案未知，返回空列表或所有条目？
             print(f"警告: 未知的筛选方案 '{scheme}'")
             return []


    def inquiry_entry(self, entry):
        """
        Increments the inquiry count for an entry and updates it using the shared Lexicon.
        """
        # 确保 entry 是字典
        if not isinstance(entry, dict):
            print("错误: inquiry_entry 接收到的 entry 不是字典。")
            return

        entry['inquiry'] = entry.get('inquiry', 0) + 1
        # --- 使用共享的 lexicon 实例来更新 ---
        if self.lexicon:
            self.lexicon.update_entry_in_defaults(entry)
        else:
            print("错误: Data.inquiry_entry 无法访问共享的 Lexicon 实例。")