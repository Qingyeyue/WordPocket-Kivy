# screens/recite_screen.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout  # 或者其他布局
from kivy.clock import Clock


# 不再需要导入 core.Lexicon
# from core.lexicon import Lexicon
from core.recite import Recite
from core.data import Data
from ui_elements.buttons import RoundButton
from ui_elements.labels import create_wrapped_label
from utils.popups import show_message, show_confirmation

class ReciteScreen(BoxLayout):
    def __init__(self, return_to_main, lexicon_instance, data_instance, **kwargs):
        super(ReciteScreen, self).__init__(**kwargs)
        self.return_to_main = return_to_main
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 10

        # 颜色定义
        self.orange1 = (1.0, 0.6, 0.0, 1.0)
        self.orange2 = (1.0, 0.7, 0.3, 1.0)

        # 2. 存储共享实例
        self.lexicon = lexicon_instance
        self.data = data_instance
        # 3. 确保没有在这里创建 self.lexicon = Lexicon() 或 self.data = Data()

        # --- 创建 Recite 实例并传递共享实例 ---
        self.recite_handler = Recite(lexicon_instance=self.lexicon, data_instance=self.data)
        # --- 不再需要 self.recite = Recite() (默认构造函数) ---

        # S状态变量
        self.lexicons_available = []  # 将在 show_lexicon_selection 中填充
        self.current_lexicon = None
        self.current_scheme = None
        self.entries = []
        self.current_index = 0
        self.session_mistakes = 0

        # 启动流程
        self.show_lexicon_selection()

    def _add_return_button(self, back_action):
        """Helper to add a consistent return button."""
        return_button = RoundButton(text='返回', size_hint=(1, None), height=80)
        return_button.bind(on_press=lambda btn: back_action())
        # Add it to the main layout, assuming it's the last element desired
        if self.children: # Check if layout has children
            self.add_widget(return_button)
        else: # If layout cleared, need to ensure it gets added
            Clock.schedule_once(lambda dt: self.add_widget(return_button), 0)

    def show_lexicon_selection(self):
        self.clear_widgets()
        self.add_widget(Label(text="选择要背诵的词库", size_hint_y=None, height=60, font_size=24))

        scroll = ScrollView(size_hint=(1, 1))
        grid = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        grid.bind(minimum_height=grid.setter('height'))

        button_height = 100

        # --- 使用 self.lexicon 获取列表 ---
        self.lexicons_available = self.lexicon.get_lexicon_list()

        if not self.lexicons_available:
            grid.add_widget(Label(text="未未找到自定义词库。\n请先在'词库'界面创建。", halign='center'))
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
                # show_scheme_selection 不需要修改，因为它只传递名字
                button.bind(on_press=lambda btn: self.show_scheme_selection(btn.lexicon_name))
                grid.add_widget(button)

        scroll.add_widget(grid)
        self.add_widget(scroll)
        self._add_return_button(self.return_to_main)

    def show_scheme_selection(self, lexicon_name):
        self.current_lexicon = lexicon_name
        self.clear_widgets()
        self.add_widget(Label(text=f"词库: {lexicon_name}\n选择背诵方案", size_hint_y=None, height=80, font_size=24, halign='center'))

        scroll = ScrollView(size_hint=(1, 1))
        grid = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        grid.bind(minimum_height=grid.setter('height'))

        button_height = 100

        # --- 使用 self.lexicon 获取条目 (用于计算数量) ---
        # 注意: get_lexicon_entries 现在由 Lexicon 实例处理映射
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
             # 注意 filter_entries 是 Data 的静态方法，不需要 self.data 实例
             # 但如果 filter_entries 将来需要访问 data 实例属性，就需要 self.data.filter_entries
             filtered_entries = Data.filter_entries(entries, scheme)
             count = len(filtered_entries)

             if count == 0 and scheme != 'all': continue # 跳过空方案

             bg_color = self.orange1 if index % 2 == 0 else self.orange2
             button = RoundButton(
                 text=f"{label} ({count})",
                 size_hint_y=None,
                 height=button_height,
                 bg_color=bg_color,
                 disabled=(count == 0)  # Disable if count is 0
             )
             button.scheme = scheme
             # show_count_selection 不需要修改
             button.bind(on_press=lambda btn: self.show_count_selection(btn.scheme))
             grid.add_widget(button)

        scroll.add_widget(grid)
        self.add_widget(scroll)
        self._add_return_button(self.show_lexicon_selection) # Return to lexicon selection

    def show_count_selection(self, scheme):
        self.current_scheme = scheme
        self.clear_widgets()
        self.add_widget(Label(text=f"方案: {scheme}\n选择背诵数量", size_hint_y=None, height=80, font_size=24, halign='center'))

        scroll = ScrollView(size_hint=(1, 1))
        grid = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        grid.bind(minimum_height=grid.setter('height'))

        button_height = 100

        # --- 获取最大可用数量 (需要 lexicon 和 data) ---
        max_count = 0
        try:
            entries = self.lexicon.get_lexicon_entries(self.current_lexicon)
            # 使用 Data 的静态方法
            filtered_entries = Data.filter_entries(entries, self.current_scheme)
            max_count = len(filtered_entries)
        except Exception as e:
            print(f"计算最大数量时出错: {e}")

        counts = [10, 20, 30, 50, '全部']
        if max_count == 0:
            grid.add_widget(Label(text="该方案下无可用词条", halign='center'))
        else:
            for index, count in enumerate(counts):
                bg_color = self.orange1 if index % 2 == 0 else self.orange2
                display_count = count
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
                # prepare_recite_session 不需要修改
                button.bind(on_press=lambda btn: self.prepare_recite_session(btn.count))
                grid.add_widget(button)

        scroll.add_widget(grid)
        self.add_widget(scroll)
        self._add_return_button(lambda: self.show_scheme_selection(self.current_lexicon))

    def prepare_recite_session(self, count):
        # --- 使用 self.recite_handler (它内部会使用共享的 lexicon 和 data) ---
        self.entries, sufficient = self.recite_handler.get_filtered_entries(
            self.current_lexicon, self.current_scheme, count
        )

        if not self.entries:
             show_message("无法获取词条，请检查词库和方案。", title="错误")
             self.show_scheme_selection(self.current_lexicon)
             return

        if not sufficient:
            show_confirmation(
                f'可用条目不足 ({len(self.entries)}条)，\n是否继续？',
                on_confirm=self.begin_recite, # Pass method reference
                title='数量不足'
            )
        else:
            self.begin_recite()

    def begin_recite(self): # No longer needs entries passed directly
        self.current_index = 0
        self.session_mistakes = 0
        self.show_entry_card() # Switch to the card display

    def show_entry_card(self):
        if self.current_index >= len(self.entries):
            self.show_summary()
            return

        entry = self.entries[self.current_index]
        self.clear_widgets()

        card_layout = FloatLayout()

        progress_text = f"{self.current_index + 1} / {len(self.entries)}"
        progress_label = Label(text=progress_text, size_hint=(None, None), size=(200, 50),
                               pos_hint={'center_x': 0.5, 'top': 1})
        card_layout.add_widget(progress_label)

        chinese_label = create_wrapped_label(
            text=f"{entry.get('chinese', 'N/A')}",
            font_size=40, # Adjust as needed
            size_hint=(0.9, 0.6), # Take 90% width, 60% height
            pos_hint={'center_x': 0.5, 'center_y': 0.6}, # Position in upper-middle
            halign='center', valign='middle' # Center text within label bounds
            )
        card_layout.add_widget(chinese_label)


        # Bottom Button Bar
        button_bar_height = 100
        button_bar = BoxLayout(
            size_hint=(1, None), height=button_bar_height,
            pos_hint={'center_x': 0.5, 'y': 0}, # Anchor to bottom
            spacing=10, padding=10
        )

        pass_button = RoundButton(text='认识', bg_color=(0.1, 0.7, 0.1, 1))
        view_button = RoundButton(text='查看', bg_color=(0.1, 0.5, 0.8, 1))
        # Removed 'Return' during recite, add 'Finish Early' if needed

        button_bar.add_widget(pass_button)
        button_bar.add_widget(view_button)
        card_layout.add_widget(button_bar)

        # --- 绑定动作到 update_entry_state 和 show_entry_details_popup ---
        # 这两个方法会使用 self.recite_handler 或显示弹窗
        pass_button.bind(on_press=lambda btn: self.update_entry_state('pass'))
        view_button.bind(on_press=lambda btn: self.show_entry_details_popup(entry))  # entry 是当前条目

        self.add_widget(card_layout)

    def show_entry_details_popup(self, entry):
        main_layout = BoxLayout(orientation='vertical', spacing=5, padding=10)

        scroll_content = ScrollView(size_hint=(1, 0.8))
        content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content_box.bind(minimum_height=content_box.setter('height'))

        label_font_size = 20

        content_box.add_widget(create_wrapped_label(f"中: {entry.get('chinese', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"英: {entry.get('english', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"备注: {entry.get('note', '')}", font_size=label_font_size))

        scroll_content.add_widget(content_box)
        main_layout.add_widget(scroll_content)

        # 添加滚动视图和标签显示 entry 内容
        buttons_layout = BoxLayout(size_hint=(1, None), height=80, spacing=10)
        knew_it_button = RoundButton(text='认识了', bg_color=(0.1, 0.7, 0.1, 1))
        mistake_button = RoundButton(text='不认识', bg_color=(0.9, 0.2, 0.2, 1))

        buttons_layout.add_widget(knew_it_button)
        buttons_layout.add_widget(mistake_button)
        main_layout.add_widget(buttons_layout)

        # --- Popup Creation ---
        detail_popup = Popup(
            title='条目详情',
            content=main_layout,
            size_hint=(0.85, 0.7),
            auto_dismiss=False  # User must choose an action
        )

        # “认识了”按钮：关闭弹窗，并以 'view' 类型更新状态（表示看过后认识了）
        knew_it_button.bind(on_press=lambda btn: (detail_popup.dismiss(), self.update_entry_state('view')))
        # “不认识”按钮：关闭当前弹窗，并调用 show_mistake_details 显示包含统计信息的最终确认弹窗
        mistake_button.bind(on_press=lambda btn: (detail_popup.dismiss(), self.show_mistake_details(entry)))

        detail_popup.open()

    def show_mistake_confirmation(self, entry):
        """Optional: Show stats before confirming mistake. Or just update directly."""
        # Simplified: Directly mark as mistake without extra stats popup
        self.update_entry_state('mistake')

        # --- If you want the mistake details popup (like original): ---
        # main_layout = BoxLayout(orientation='vertical', spacing=5, padding=10)
        # scroll_content = ScrollView(size_hint=(1, 0.8))
        # content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        # content_box.bind(minimum_height=content_box.setter('height'))
        # label_font_size = 18
        # content_box.add_widget(create_wrapped_label(f"中: {entry.get('chinese', '')}", font_size=label_font_size))
        # content_box.add_widget(create_wrapped_label(f"英: {entry.get('english', '')}", font_size=label_font_size))
        # content_box.add_widget(create_wrapped_label(f"备注: {entry.get('note', '')}", font_size=label_font_size))
        # content_box.add_widget(create_wrapped_label(f"查询: {entry.get('inquiry', 0)} | 记忆: {entry.get('memory', 0)} | 错误: {entry.get('mistake', 0)+1}", font_size=label_font_size - 4)) # Show potential new count
        # scroll_content.add_widget(content_box)
        # main_layout.add_widget(scroll_content)
        # confirm_button = RoundButton(text='确认(不认识)', size_hint_y=None, height=80, bg_color=(0.9, 0.2, 0.2, 1))
        # main_layout.add_widget(confirm_button)
        # mistake_popup = Popup(title='确认错误', content=main_layout, size_hint=(0.85, 0.7), auto_dismiss=False)
        # confirm_button.bind(on_press=lambda btn: (mistake_popup.dismiss(), self.update_entry_state('mistake')))
        # mistake_popup.open()

    def update_entry_state(self, update_type):
        """Updates the entry state using Recite handler and advances."""
        if self.current_index < len(self.entries):
            entry = self.entries[self.current_index]

            if update_type == 'mistake':
                self.session_mistakes += 1

            self.recite_handler.update_entry(entry, update_type)

            self.current_index += 1
            # 延迟调用 show_entry_card，确保弹窗完全关闭后再刷新界面，避免闪烁
            Clock.schedule_once(lambda dt: self.show_entry_card(), 0.1) # 延迟0.1秒
        else:
            # 延迟调用 show_summary
            Clock.schedule_once(lambda dt: self.show_summary(), 0.1)

    def show_summary(self):
        self.clear_widgets()

        total = len(self.entries)
        # Use session mistakes for summary, not persistent entry['mistake']
        mistakes = self.session_mistakes
        correct = total - mistakes
        accuracy = (correct / total * 100) if total > 0 else 0

        # --- Summary Layout ---
        summary_layout = BoxLayout(orientation='vertical', spacing=15, padding=30)

        summary_layout.add_widget(Label(text="背诵结束", font_size=30, size_hint_y=None, height=50))

        summary_layout.add_widget(create_wrapped_label(f"总条目数: {total}", font_size=22))
        summary_layout.add_widget(create_wrapped_label(f"认识: {correct}", font_size=22))
        summary_layout.add_widget(create_wrapped_label(f"不认识: {mistakes}", font_size=22))
        summary_layout.add_widget(create_wrapped_label(f"正确率: {accuracy:.1f}%", font_size=22))

        # Spacer to push button to bottom
        summary_layout.add_widget(BoxLayout(size_hint_y=1)) # Fills remaining space

        # Return Button
        return_button = RoundButton(text='完成返回', size_hint=(1, None), height=100)
        # Go back to the initial lexicon selection for ReciteScreen
        return_button.bind(on_press=lambda btn: self.show_lexicon_selection())
        summary_layout.add_widget(return_button)

        self.add_widget(summary_layout)

    def show_mistake_details(self, entry):
        """显示包含统计信息的错误确认弹窗。"""
        main_layout = BoxLayout(orientation='vertical', spacing=5, padding=10)

        scroll_content = ScrollView(size_hint=(1, 0.8))  # 留出底部按钮空间
        content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content_box.bind(minimum_height=content_box.setter('height'))

        label_font_size = 18  # 可以稍微小一点

        # 显示所有信息，包括统计数据
        content_box.add_widget(create_wrapped_label(f"中: {entry.get('chinese', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"英: {entry.get('english', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"备注: {entry.get('note', '')}", font_size=label_font_size))
        # 显示当前的统计数据 (错误次数会在 update_entry_state 中 +1)
        content_box.add_widget(
            create_wrapped_label(f"查询次数: {entry.get('inquiry', 0)}", font_size=label_font_size - 2))
        content_box.add_widget(
            create_wrapped_label(f"记忆次数: {entry.get('memory', 0)}", font_size=label_font_size - 2))
        content_box.add_widget(
            create_wrapped_label(f"错误次数: {entry.get('mistake', 0)}", font_size=label_font_size - 2))

        scroll_content.add_widget(content_box)
        main_layout.add_widget(scroll_content)

        # 添加确认按钮
        # 这个按钮的功能是：关闭这个弹窗，并以 'mistake' 类型更新状态，进入下一个词
        confirm_button = RoundButton(text='确认(不认识)', size_hint_y=None, height=80, bg_color=(0.9, 0.2, 0.2, 1))
        main_layout.add_widget(confirm_button)

        # 创建弹窗
        mistake_popup = Popup(
            title='错误确认',  # 或者叫“详细信息”
            content=main_layout,
            size_hint=(0.85, 0.7),  # 大小可以调整
            auto_dismiss=False  # 需要用户点击按钮
        )

        # 绑定确认按钮的动作
        confirm_button.bind(on_press=lambda btn: (mistake_popup.dismiss(), self.update_entry_state('mistake')))

        mistake_popup.open()