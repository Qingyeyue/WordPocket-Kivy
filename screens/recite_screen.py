# screens/recite_screen.py
import random # 导入 random 用于打乱列表
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout # 或者其他布局
from kivy.clock import Clock
from kivy.properties import StringProperty # 导入 StringProperty

# 不再需要导入 core.Lexicon
# from core.lexicon import Lexicon
from core.recite import Recite
from core.data import Data
from ui_elements.buttons import RoundButton
from ui_elements.labels import create_wrapped_label
from utils.popups import show_message, show_confirmation

class ReciteScreen(BoxLayout):
    # 使用 Kivy Property 可以让绑定更方便，尽管在这个例子里可能不是必须的
    recite_direction = StringProperty('zh_en') # 'zh_en' for Chinese->English, 'en_zh' for English->Chinese

    def __init__(self, return_to_main, lexicon_instance, data_instance, **kwargs):
        super(ReciteScreen, self).__init__(**kwargs)
        self.return_to_main = return_to_main
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 10

        # 颜色定义
        self.orange1 = (1.0, 0.6, 0.0, 1.0)
        self.orange2 = (1.0, 0.7, 0.3, 1.0)
        self.green = (0.1, 0.7, 0.1, 1)
        self.red = (0.9, 0.2, 0.2, 1)
        self.blue = (0.1, 0.5, 0.8, 1)
        self.gray = (0.5, 0.5, 0.5, 1)

        # 2. 存储共享实例
        self.lexicon = lexicon_instance
        self.data = data_instance

        # --- 创建 Recite 实例并传递共享实例 ---
        self.recite_handler = Recite(lexicon_instance=self.lexicon, data_instance=self.data)

        # 状态变量
        self.lexicons_available = []
        self.current_lexicon = None
        self.current_scheme = None
        # 背诵列表相关的状态
        self.initial_session_entries = [] # 第一次筛选出来的完整列表
        self.current_recite_list = [] # 当前轮次要背诵的列表 (可能是 initial 或 mistake list)
        self.mistakes_in_this_attempt = [] # 当前轮次中标记错误的词条
        self.session_mistakes = 0 # 整个背诵环节（包括所有重背轮次）累计的错误数 (只在第一轮增加)
        self.current_index = 0
        self.is_first_pass = True # 标记是否是第一轮背诵 (用于控制统计更新)

        # 启动流程：先显示方向选择
        self.show_direction_selection()

    def _add_return_button(self, back_action, text="返回"):
        """Helper to add a consistent return button."""
        return_button = RoundButton(text=text, size_hint=(1, None), height=150, bg_color=self.gray)
        return_button.bind(on_press=lambda btn: back_action())
        # Add it to the main layout, assuming it's the last element desired
        self.add_widget(return_button)

    def show_direction_selection(self):
        """Displays the screen for selecting recitation direction."""
        self.clear_widgets()
        self.add_widget(Label(text="选择背诵方向", size_hint_y=None, height=200, font_size=50, halign='center', valign='middle'))

        direction_layout = BoxLayout(orientation='vertical', size_hint_y=1, spacing=20, padding=20)
        button_height = 200

        # 中文 -> 英文
        zh_en_button = RoundButton(text="中文 → 英文", size_hint_y=None, height=button_height, bg_color=self.blue)
        zh_en_button.bind(on_press=lambda btn: self._select_direction('zh_en'))
        direction_layout.add_widget(zh_en_button)

        # 英文 -> 中文
        en_zh_button = RoundButton(text="英文 → 中文", size_hint_y=None, height=button_height, bg_color=self.orange1)
        en_zh_button.bind(on_press=lambda btn: self._select_direction('en_zh'))
        direction_layout.add_widget(en_zh_button)

        self.add_widget(direction_layout)

        # 返回主页按钮
        self._add_return_button(self.return_to_main, text="返回主页")


    def _select_direction(self, direction):
        """Sets the recitation direction and proceeds to lexicon selection."""
        self.recite_direction = direction
        print(f"背诵方向设置为: {'中文 -> 英文' if direction == 'zh_en' else '英文 -> 中文'}")
        self.show_lexicon_selection()

    def show_lexicon_selection(self):
        """Displays the list of available lexicons."""
        self.clear_widgets()
        self.add_widget(Label(text=f"背诵方向: {'中文 → 英文' if self.recite_direction == 'zh_en' else '英文 → 中文'}\n选择要背诵的词库", size_hint_y=None, height=200, font_size=50, halign='center', valign='middle'))

        scroll = ScrollView(size_hint=(1, 1))
        grid = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        grid.bind(minimum_height=grid.setter('height'))

        button_height = 150

        # --- 使用 self.lexicon 获取列表 ---
        self.lexicons_available = self.lexicon.get_lexicon_list()

        if not self.lexicons_available:
            grid.add_widget(Label(text="未未找到自定义词库。\n请先在'词库'界面创建。", halign='center', valign='middle'))
        else:
            for index, lexicon_name in enumerate(self.lexicons_available):
                entry_count = 'N/A'  # 获取数量可能需要加载，这里先简化
                try:
                    # 尝试加载索引数量，避免加载完整条目
                    indices = self.lexicon.load_lexicon(lexicon_name)
                    entry_count = len(indices)
                except Exception as e:
                    print(f"获取词库 '{lexicon_name}' 条目数时出错: {e}")

                bg_color = self.orange1 if index % 2 == 0 else self.orange2
                button = RoundButton(
                    text=f"{lexicon_name} ({entry_count})",
                    size_hint_y=None,
                    height=button_height,
                    bg_color=bg_color
                )
                button.lexicon_name = lexicon_name
                button.bind(on_press=lambda btn: self.show_scheme_selection(btn.lexicon_name))
                grid.add_widget(button)

        scroll.add_widget(grid)
        self.add_widget(scroll)
        # 返回到方向选择界面
        self._add_return_button(self.show_direction_selection)

    def show_scheme_selection(self, lexicon_name):
        """Displays scheme selection for the chosen lexicon."""
        self.current_lexicon = lexicon_name
        self.clear_widgets()
        self.add_widget(Label(text=f"词库: {lexicon_name}\n选择背诵方案", size_hint_y=None, height=200, font_size=50, halign='center', valign='middle'))

        scroll = ScrollView(size_hint=(1, 1))
        grid = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        grid.bind(minimum_height=grid.setter('height'))

        button_height = 150

        # --- 使用 self.lexicon 获取条目 (用于计算数量) ---
        try:
            entries = self.lexicon.get_lexicon_entries(lexicon_name)
        except Exception as e:
            entries = []
            show_message(f"加载词库 '{lexicon_name}' 条目时出错: {e}", title="加载错误")
            self.show_lexicon_selection()  # 返回上一步
            return

        schemes = [('新鲜词', 'new'), ('巩固词', 'consolidate'), ('复习词', 'review'), ('所有词', 'all')]

        for index, (label, scheme) in enumerate(schemes):
             # --- 使用 self.data 筛选条目 (静态方法) ---
             filtered_entries = Data.filter_entries(entries, scheme)
             count = len(filtered_entries)

             if count == 0 and scheme != 'all': continue # 跳过空方案，除非是所有词

             bg_color = self.orange1 if index % 2 == 0 else self.orange2
             button = RoundButton(
                 text=f"{label} ({count})",
                 size_hint_y=None,
                 height=button_height,
                 bg_color=bg_color,
                 disabled=(count == 0 and scheme != 'all')  # Disable if count is 0 (except 'all')
             )
             button.scheme = scheme
             button.bind(on_press=lambda btn: self.show_count_selection(btn.scheme))
             grid.add_widget(button)

        scroll.add_widget(grid)
        self.add_widget(scroll)
        # 返回到词库选择界面
        self._add_return_button(self.show_lexicon_selection)

    def show_count_selection(self, scheme):
        """Displays count selection for the chosen scheme."""
        self.current_scheme = scheme
        self.clear_widgets()
        self.add_widget(Label(text=f"词库: {self.current_lexicon}\n方案: {scheme}\n选择背诵数量", size_hint_y=None, height=200, font_size=50, halign='center', valign='middle'))

        scroll = ScrollView(size_hint=(1, 1))
        grid = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        grid.bind(minimum_height=grid.setter('height'))

        button_height = 150

        # --- 获取最大可用数量 (需要 lexicon 和 data) ---
        max_count = 0
        try:
            entries = self.lexicon.get_lexicon_entries(self.current_lexicon)
            # 使用 Data 的静态方法
            filtered_entries = Data.filter_entries(entries, self.current_scheme)
            max_count = len(filtered_entries)
        except Exception as e:
            print(f"计算最大数量时出错: {e}")

        counts = [1, 5, 10, 20, 30, 50, '全部']
        if max_count == 0:
            grid.add_widget(Label(text="该方案下无可用词条", halign='center'))
        else:
            for index, count in enumerate(counts):
                bg_color = self.orange1 if index % 2 == 0 else self.orange2
                actual_count = count

                if count == '全部':
                    actual_count = max_count
                    display_text = f"全部 ({actual_count})"
                elif count > max_count:
                    # Don't show options greater than available, except 'All'
                    continue
                else:
                    display_text = str(count)

                button = RoundButton(
                    text=display_text,
                    size_hint_y=None,
                    height=button_height,
                    bg_color=bg_color
                )
                button.count = actual_count
                button.bind(on_press=lambda btn: self.prepare_recite_session(btn.count))
                grid.add_widget(button)

        scroll.add_widget(grid)
        self.add_widget(scroll)
        # 返回到方案选择界面
        self._add_return_button(lambda: self.show_scheme_selection(self.current_lexicon))

    def prepare_recite_session(self, count):
        """Prepares entries for the first recitation attempt."""
        # --- 使用 self.recite_handler 获取词条 ---
        entries, sufficient = self.recite_handler.get_filtered_entries(
            self.current_lexicon, self.current_scheme, count
        )

        if not entries:
             show_message("无法获取词条，请检查词库和方案。", title="错误")
             self.show_scheme_selection(self.current_lexicon)
             return

        # 随机打乱词条列表
        random.shuffle(entries)

        # 初始化背诵状态
        self.initial_session_entries = entries.copy() # 存储原始列表用于总结
        self.current_recite_list = entries # 当前轮次背诵列表，开始是原始列表
        self.current_index = 0
        self.session_mistakes = 0 # 总错误数，第一轮开始时清零
        self.is_first_pass = True # 标记是第一轮
        self.mistakes_in_this_attempt = [] # 当前轮次的错误列表

        if not sufficient:
            show_confirmation(
                f'可用条目不足 ({len(self.current_recite_list)}条)，\n是否继续？',
                on_confirm=self.begin_recite_attempt, # 确认后开始背诵
                title='数量不足'
            )
        else:
            self.begin_recite_attempt() # 直接开始背诵


    def begin_recite_attempt(self):
        """Starts a new attempt (either the initial session or a mistake review round)."""
        if not self.current_recite_list:
            # Should not happen if called correctly after prepare/end_attempt
            print("Warning: begin_recite_attempt called with empty list.")
            self.show_summary() # Go to summary if somehow list is empty
            return

        self.current_index = 0
        self.mistakes_in_this_attempt = [] # 清空当前轮次的错误记录

        # 显示开始新一轮的提示
        if not self.is_first_pass:
             show_message(f"开始新一轮纠错，共 {len(self.current_recite_list)} 个词条。", title="开始纠错")
             # Add a small delay before showing the first card
             Clock.schedule_once(lambda dt: self.show_entry_card(), 1.0) # 延迟1秒
        else:
             # 如果是第一轮，直接显示卡片
             self.show_entry_card()

    def show_entry_card(self):
        """Displays the current entry card."""
        if self.current_index >= len(self.current_recite_list):
            # Current attempt finished, process results
            self.end_current_attempt()
            return

        entry = self.current_recite_list[self.current_index]
        self.clear_widgets()

        card_layout = FloatLayout()

        # Progress Label
        progress_text = f"轮次进度: {self.current_index + 1} / {len(self.current_recite_list)}"
        if self.is_first_pass:
             progress_text = f"总进度: {self.current_index + 1} / {len(self.current_recite_list)}"
        else:
             progress_text = f"纠错轮次: {self.current_index + 1} / {len(self.current_recite_list)}\n当前轮次错误: {len(self.mistakes_in_this_attempt)}"


        progress_label = Label(text=progress_text, size_hint=(None, None), size=(400, 100),
                               pos_hint={'center_x': 0.5, 'top': 1},
                               halign='center', valign='middle')
        card_layout.add_widget(progress_label)

        # Display Text based on direction
        prompt_text = entry.get('chinese', 'N/A') if self.recite_direction == 'zh_en' else entry.get('english', 'N/A')
        prompt_label = create_wrapped_label(
            text=prompt_text,
            font_size=150, # Adjust as needed
            size_hint=(0.9, 0.6), # Take 90% width, 60% height
            pos_hint={'center_x': 0.5, 'center_y': 0.6}, # Position in upper-middle
            halign='center', valign='middle' # Center text within label bounds
        )
        card_layout.add_widget(prompt_label)


        # Bottom Button Bar
        button_bar_height = 150
        button_bar = BoxLayout(
            size_hint=(1, None), height=button_bar_height,
            pos_hint={'center_x': 0.5, 'y': 0}, # Anchor to bottom
            spacing=10, padding=10
        )

        # "认识" 按钮 - 直接跳到下一个词 (标记为pass)
        pass_button = RoundButton(text='认识', bg_color=self.green)
        # "查看/不认识" 按钮 - 显示详情弹窗
        view_mistake_button = RoundButton(text='查看 / 不认识', bg_color=self.blue)
        # "提前结束" 按钮
        end_session_button = RoundButton(text='提前结束', bg_color=self.red)


        button_bar.add_widget(pass_button)
        button_bar.add_widget(view_mistake_button)
        button_bar.add_widget(end_session_button) # Add end session button
        card_layout.add_widget(button_bar)

        # --- 绑定动作 ---
        pass_button.bind(on_press=lambda btn: self.update_entry_and_continue('pass', entry))
        view_mistake_button.bind(on_press=lambda btn: self.show_entry_details_popup(entry))
        end_session_button.bind(on_press=lambda btn: show_confirmation(
            "确定要提前结束本次背诵吗？",
            on_confirm=self.show_summary, # 直接跳到总结
            title="提前结束"
        ))

        self.add_widget(card_layout)

    def update_entry_and_continue(self, update_type, entry):
        """Updates entry state and proceeds to the next card/attempt."""
        # Only update stats on the first pass
        update_stats_in_core = self.is_first_pass

        if update_type == 'mistake':
            # Record mistake for the current attempt's mistake list
            self.mistakes_in_this_attempt.append(entry)
            # Increment total session mistakes ONLY on the first pass
            if self.is_first_pass:
                 self.session_mistakes += 1
        elif update_type == 'view':
             # 'view' means they saw the answer and might have recognized it then.
             # We count this as 'memory' and 'inquiry', but NOT 'mistake'.
             # It doesn't add to mistakes_in_this_attempt.
             pass # Logic is handled inside Recite handler based on update_type

        # Use the recite handler to update the entry in defaults.
        # Pass the flag to control whether stats are incremented in core.
        self.recite_handler.update_entry(entry, update_type, update_stats=update_stats_in_core)

        # Move to the next index in the current list
        self.current_index += 1

        # Schedule the next action (show next card or end attempt)
        # Use Clock.schedule_once to ensure popups close cleanly before refreshing
        Clock.schedule_once(lambda dt: self.show_entry_card(), 0.1)

    def end_current_attempt(self):
        """Handles logic when an attempt (a pass through current_recite_list) ends."""
        if not self.mistakes_in_this_attempt:
            # No mistakes in this attempt - the loop is finished (for this set of words)
            show_message("本轮全部背诵正确！", title="完成")
            # Add a small delay before showing summary
            Clock.schedule_once(lambda dt: self.show_summary(), 1.0) # 延迟1秒
        else:
            # There were mistakes in this attempt - start a new attempt with just the mistakes
            print(f"Attempt ended. {len(self.mistakes_in_this_attempt)} mistakes.")
            self.current_recite_list = self.mistakes_in_this_attempt # The new list is the mistakes from this attempt
            self.is_first_pass = False # All subsequent rounds are not the first pass
            # Start the next attempt with the mistakes list
            self.begin_recite_attempt()


    def show_entry_details_popup(self, entry):
        """Shows entry details, including stats (as they were before this card)."""
        main_layout = BoxLayout(orientation='vertical', spacing=5, padding=10)

        # Scrollable content area
        scroll_content = ScrollView(size_hint=(1, 0.8))
        content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content_box.bind(minimum_height=content_box.setter('height'))

        label_font_size = 100 # Adjust size as needed

        # Display all information regardless of recite direction
        content_box.add_widget(create_wrapped_label(f"中文: {entry.get('chinese', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"英文: {entry.get('english', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"备注: {entry.get('note', '')}", font_size=label_font_size))

        # Display CURRENT stats (before this card's outcome is recorded)
        # Stats will be updated in update_entry_and_continue after popup closes
        content_box.add_widget(
            create_wrapped_label(f"统计:\n查询次数: {entry.get('inquiry', 0)}\n记忆次数: {entry.get('memory', 0)}\n错误次数: {entry.get('mistake', 0)}", font_size=label_font_size - 10))

        scroll_content.add_widget(content_box)
        main_layout.add_widget(scroll_content)

        # Action Buttons at the bottom
        buttons_layout = BoxLayout(size_hint=(1, 0.2), height=150, spacing=10) # 20% height
        # Button for user action after seeing details
        knew_after_view_btn = RoundButton(text='看到答案后认识了', bg_color=self.green)
        mistake_confirm_btn = RoundButton(text='不认识 / 记错了', bg_color=self.red)


        buttons_layout.add_widget(knew_after_view_btn)
        buttons_layout.add_widget(mistake_confirm_btn)
        main_layout.add_widget(buttons_layout)

        # --- Popup Creation ---
        detail_popup = Popup(
            title='条目详情',
            content=main_layout,
            size_hint=(0.9, 0.8), # Slightly wider
            auto_dismiss=False # User must choose an action
        )

        # --- 绑定按钮动作 ---
        # "看到答案后认识了" -> Update as 'view', proceed to next card
        knew_after_view_btn.bind(on_press=lambda btn: (detail_popup.dismiss(), self.update_entry_and_continue('view', entry)))
        # "不认识 / 记错了" -> Update as 'mistake', proceed to next card
        mistake_confirm_btn.bind(on_press=lambda btn: (detail_popup.dismiss(), self.update_entry_and_continue('mistake', entry)))


        detail_popup.open()

    def show_summary(self):
        """Displays the recitation session summary."""
        self.clear_widgets()

        initial_total = len(self.initial_session_entries)
        # Use the total session mistakes accumulated ONLY in the first pass
        total_mistakes = self.session_mistakes
        correct_in_first_pass = initial_total - total_mistakes
        accuracy = (correct_in_first_pass / initial_total * 100) if initial_total > 0 else 0

        # --- Summary Layout ---
        summary_layout = BoxLayout(orientation='vertical', spacing=15, padding=30)

        summary_layout.add_widget(Label(text="背诵结束", font_size=150, size_hint_y=None, height=200, halign='center', valign='middle'))

        summary_layout.add_widget(create_wrapped_label(f"本次背诵总条目数: {initial_total}", font_size=100))
        summary_layout.add_widget(create_wrapped_label(f"第一轮认识(或查看后认识): {initial_total - self.session_mistakes}", font_size=100)) # Correct in first pass includes 'pass' and 'view'
        summary_layout.add_widget(create_wrapped_label(f"第一轮不认识: {self.session_mistakes}", font_size=100)) # Total mistakes recorded in first pass
        summary_layout.add_widget(create_wrapped_label(f"第一轮正确率: {accuracy:.1f}%", font_size=100))
        if not self.is_first_pass: # If there were review rounds
             summary_layout.add_widget(create_wrapped_label("所有错误词条均已背诵正确！", font_size=100, color=self.green))


        # Spacer to push button to bottom
        summary_layout.add_widget(BoxLayout(size_hint_y=1)) # Fills remaining space

        # Return Button
        # Go back to the initial direction selection for ReciteScreen
        self._add_return_button(self.show_direction_selection, text='完成返回')

        self.add_widget(summary_layout)

    # We no longer need a separate show_mistake_details as show_entry_details_popup serves this
    # def show_mistake_details(self, entry): ...
