# core/recite.py
import random
# 不再需要从这里导入 Lexicon 或 Data
# from core.lexicon import Lexicon
# from core.data import Data

class Recite:
    # 修改 __init__ 以接收共享实例
    def __init__(self, lexicon_instance, data_instance):
        """
        Initializes the Recite handler with shared Lexicon and Data instances.

        Args:
            lexicon_instance: The shared instance of the Lexicon class.
            data_instance: The shared instance of the Data class.
        """
        # --- 存储共享实例 ---
        self.lexicon = lexicon_instance
        self.data = data_instance
        # --- 不再需要 self.lexicon = Lexicon(...) ---
        # --- 不再需要 self.data = Data() ---
        # --- 也不再需要 self.default_lexicon 或 lexicon_dir ---

    # get_words 和 recite_words 可能不再需要，因为主要逻辑在 get_filtered_entries
    # def get_words(self, lexicon_name=None, n=10): ...
    # def recite_words(self, lexicon_name=None, n=10): ...

    def get_filtered_entries(self, lexicon_name, scheme, count):
        """
        Gets entries from a specified lexicon, filters them based on a scheme,
        and returns a random sample. Uses shared Lexicon and Data instances.
        """
        if not self.lexicon or not self.data:
             print("错误: Recite 无法访问共享的 Lexicon 或 Data 实例。")
             return [], False # 返回空列表和 False

        # --- 使用共享的 lexicon 实例获取条目 ---
        # get_lexicon_entries 已经处理了索引到字典的映射
        entries = self.lexicon.get_lexicon_entries(lexicon_name)
        if not entries:
             print(f"信息: 词库 '{lexicon_name}' 为空或加载失败。")
             return [], False # 返回空

        # --- 使用共享的 data 实例进行筛选 ---
        filtered_entries = self.data.filter_entries(entries, scheme)
        if not filtered_entries:
             print(f"信息: 在词库 '{lexicon_name}' 中根据方案 '{scheme}' 未找到符合条件的条目。")
             return [], False # 返回空

        actual_count = len(filtered_entries)
        sufficient = actual_count >= count

        # 取样：如果请求数量大于实际数量，则返回所有筛选出的条目
        sample_count = min(count, actual_count)
        sampled_entries = random.sample(filtered_entries, sample_count)

        # 返回取样结果和是否足够
        return sampled_entries, sufficient


    def update_entry(self, entry, update_type):
        """
        Updates an entry's statistics based on the recitation result ('pass', 'view', 'mistake')
        and saves the change using the shared Lexicon instance.
        """
        if not self.lexicon:
             print("错误: Recite.update_entry 无法访问共享的 Lexicon 实例。")
             return
        if not isinstance(entry, dict):
            print("错误: Recite.update_entry 接收到的 entry 不是字典。")
            return

        # 更新统计数据
        # 注意: .get(key, 0) 确保即使键不存在也能安全地 +1
        if update_type == 'pass':
            entry['memory'] = entry.get('memory', 0) + 1
        elif update_type == 'view':
            # 查看也算一次记忆，可能也算一次查询？根据您的定义调整
            entry['memory'] = entry.get('memory', 0) + 1
            entry['inquiry'] = entry.get('inquiry', 0) + 1
        elif update_type == 'mistake':
            # 错误时，通常也算记忆了一次，算查询了一次，并且错误次数+1
            entry['memory'] = entry.get('memory', 0) + 1
            entry['inquiry'] = entry.get('inquiry', 0) + 1
            entry['mistake'] = entry.get('mistake', 0) + 1
        else:
            print(f"警告: Recite.update_entry 收到未知的 update_type: {update_type}")
            # 可能不需要更新，直接返回
            return

        # --- 使用共享的 lexicon 实例保存更新 ---
        self.lexicon.update_entry_in_defaults(entry)