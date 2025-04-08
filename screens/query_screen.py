# screens/query_screen.py
import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock

# 不再需要导入 core.Lexicon 或 core.Data
# from core.data import Data
# from core.lexicon import Lexicon
from ui_elements.buttons import RoundButton
from ui_elements.labels import create_wrapped_label
from utils.popups import show_message  # (以及可能需要的 show_confirmation)

class QueryScreen(BoxLayout):
    def __init__(self, return_to_main, lexicon_instance, data_instance, **kwargs):
        super(QueryScreen, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.return_to_main = return_to_main

        # 2. 存储共享实例
        self.lexicon = lexicon_instance
        self.data = data_instance
        # 3. 确保没有在这里创建 self.lexicon = Lexicon() 或 self.data = Data()

        # --- UI 初始化 ---
        self.input = TextInput(hint_text='输入中文或英文', size_hint_y=0.1) # Give specific size hint
        self.add_widget(self.input)

        self.search_button = RoundButton(text='查询', size_hint_y=0.1, font_size=40, bg_color=(0, 1, 1, 1)) # Adjusted font size
        self.search_button.bind(on_press=self.search_word)
        self.add_widget(self.search_button)

        # Result label area (might be replaced by popup)
        self.result_label = Label(text='输入内容后点击查询', size_hint_y=0.7) # Allocate more space
        self.add_widget(self.result_label)

        # Return button always visible at bottom
        self.return_button = RoundButton(text='返回', size_hint_y=0.1, height=100) # Fixed height is often better here
        self.return_button.bind(on_press=self.return_to_main)
        self.add_widget(self.return_button)

        # --- 状态变量 ---
        self.all_results = []
        self.current_page = 0
        self.results_per_page = 30
        self.total_pages = 0
        self.results_popup = None
        self.lexicon_popup = None  # 添加词库的弹窗

    def search_word(self, instance):
        word = self.input.text.strip()
        if not word:
            self.result_label.text = '请输入要查询的单词'
            self.input.focus = True
            return

        # --- 使用 self.data ---
        results = self.data.search_word(word)

        if results:
            if isinstance(results, list):
                self.result_label.text = f"找到 {len(results)} 条结果，详情见弹窗。"
                self.show_results_popup(results)
            elif isinstance(results, dict):
                # If only one result, show directly or maybe still use a simplified popup?
                # For consistency, let's use the popup even for one result
                self.result_label.text = "找到 1 条结果，详情见弹窗。"
                self.show_results_popup([results]) # Wrap single dict in a list
            else:
                self.result_label.text = '未找到匹配的条目'
        else:
            self.result_label.text = '未找到匹配的条目'

    def show_results_popup(self, results):
        if self.results_popup: # Avoid multiple popups
             self.results_popup.dismiss()
             self.results_popup = None

        self.all_results = results
        self.current_page = 0
        self.total_pages = (len(results) + self.results_per_page - 1) // self.results_per_page

        layout = BoxLayout(orientation='vertical')

        # Pagination Controls
        pagination_height = 80 # Smaller controls
        pagination = BoxLayout(size_hint_y=None, height=pagination_height, spacing=5)
        self.prev_btn = RoundButton(text="<", size_hint_x=0.2, bg_color=(0.3, 0.6, 0.9, 1), disabled=True)
        self.page_label = Label(text=f"1 / {self.total_pages}", size_hint_x=0.6)
        self.next_btn = RoundButton(text=">", size_hint_x=0.2, bg_color=(0.3, 0.9, 0.6, 1), disabled=self.total_pages <= 1)
        self.prev_btn.bind(on_press=self._load_previous_page)
        self.next_btn.bind(on_press=self._load_next_page)
        pagination.add_widget(self.prev_btn)
        pagination.add_widget(self.page_label)
        pagination.add_widget(self.next_btn)

        # Scrollable Area for Results
        self.scroll_view = ScrollView(size_hint=(1, 1)) # Takes remaining space
        self.grid_layout = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))
        self.scroll_view.add_widget(self.grid_layout)

        # Close Button
        close_button = RoundButton(text='关闭', size_hint_y=None, height=pagination_height, bg_color=(0.9, 0.2, 0.2, 1))


        # Assemble Popup Layout
        layout.add_widget(pagination)
        layout.add_widget(self.scroll_view) # ScrollView fills the middle
        layout.add_widget(close_button)

        self.results_popup = Popup(
            title=f'查询结果 ({len(self.all_results)} 条)',
            content=layout,
            size_hint=(0.9, 0.85), # Slightly wider
            auto_dismiss=False
        )
        close_button.bind(on_press=self.results_popup.dismiss)
        self.results_popup.open()

        self._load_current_page_results() # Load initial page content

    def _load_current_page_results(self):
        """Loads results for the current page into the grid_layout."""
        self.grid_layout.clear_widgets()
        start = self.current_page * self.results_per_page
        end = start + self.results_per_page
        current_results = self.all_results[start:end]

        button_height = 100 # Smaller buttons for list view

        for index, result in enumerate(current_results):
            bg_color = (0.275, 0.510, 0.706, 1) if index % 2 == 0 else (0.345, 0.627, 0.827, 1)
            btn_text = self._format_button_text(result)
            btn = RoundButton(
                text=btn_text,
                size_hint_y=None,
                height=button_height,
                bg_color=bg_color,
                halign='left', # Align text left for readability
                padding=(10, 5)
            )
            btn.result_data = result # Store data directly on button
            btn.bind(on_press=self.show_entry_details_popup) # Use the detailed popup method
            self.grid_layout.add_widget(btn)

        self._update_pagination_controls()
        self.scroll_view.scroll_y = 1 # Scroll to top after loading

    def _update_pagination_controls(self):
        """Updates the text and disabled state of pagination buttons."""
        self.page_label.text = f"{self.current_page + 1} / {self.total_pages}"
        self.prev_btn.disabled = self.current_page <= 0
        self.next_btn.disabled = self.current_page >= self.total_pages - 1

    def _load_previous_page(self, instance):
        if self.current_page > 0:
            self.current_page -= 1
            self._load_current_page_results()

    def _load_next_page(self, instance):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._load_current_page_results()

    def _format_button_text(self, result):
        """Formats text for the result list buttons."""
        chinese = result.get('chinese', '')
        english = result.get('english', '')
        # Truncate smartly if needed
        max_len = 35
        text = f"中: {chinese} | 英: {english}"
        if len(text) > max_len:
            text = text[:max_len-3] + "..."
        return text

    def show_entry_details_popup(self, instance):
        """Shows entry details in a standardized popup."""
        result = instance.result_data

        # --- 使用 self.lexicon ---
        # 更新查询次数并保存 (现在由 Lexicon 实例负责)
        result['inquiry'] = result.get('inquiry', 0) + 1
        update_success = self.lexicon.update_entry_in_defaults(result)
        if not update_success:
            print(f"警告: 更新条目 {result.get('english')} 的查询次数失败。")

        # --- 弹窗布局  ---
        main_layout = BoxLayout(orientation='vertical', spacing=5, padding=10)

        # Scrollable content area
        scroll_content = ScrollView(size_hint=(1, 0.8)) # 80% height for details
        content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content_box.bind(minimum_height=content_box.setter('height'))

        label_font_size = 20 # Larger font for details popup

        content_box.add_widget(create_wrapped_label(f"中文: {result.get('chinese', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"英文: {result.get('english', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"备注: {result.get('note', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"查询: {result.get('inquiry', 0)} | 记忆: {result.get('memory', 0)} | 错误: {result.get('mistake', 0)}", font_size=label_font_size - 4)) # Combine stats

        scroll_content.add_widget(content_box)
        main_layout.add_widget(scroll_content)

        # Action Buttons at the bottom
        buttons_layout = BoxLayout(size_hint=(1, 0.2), height=80, spacing=10) # 20% height
        add_btn = RoundButton(text='加入词库', bg_color=(0.2, 0.8, 0.2, 1))
        close_btn = RoundButton(text='关闭', bg_color=(0.9, 0.2, 0.2, 1))

        buttons_layout.add_widget(add_btn)
        buttons_layout.add_widget(close_btn)
        main_layout.add_widget(buttons_layout)

        # --- Popup Creation ---
        detail_popup = Popup(
            title='条目详情',
            content=main_layout,
            size_hint=(0.85, 0.7), # Smaller height for details
            auto_dismiss=False
        )

        # --- 绑定按钮动作 ---
        add_btn.bind(on_press=lambda btn: self._show_add_to_lexicon_popup(result, detail_popup))
        close_btn.bind(on_press=detail_popup.dismiss)

        detail_popup.open()

    def _show_add_to_lexicon_popup(self, entry, parent_popup):
        # --- 使用 self.lexicon 获取列表 ---
        available_lexicons = self.lexicon.get_lexicon_list()  # 使用实例方法

        if not available_lexicons:
            show_message("没有可用的自定义词库。\n请先在“词库”界面创建。", title="无可用词库")
            return

        # --- 弹窗布局 ---
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        layout.add_widget(Label(text="选择要加入的目标词库", size_hint_y=None, height=40))

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, size_hint_y=None, spacing=10)
        grid.bind(minimum_height=grid.setter('height'))

        button_height = 80
        for lex_name in available_lexicons:
            btn = RoundButton(text=lex_name, size_hint_y=None, height=button_height)
            # Pass necessary info to the action function
            btn.bind(on_press=lambda instance, l=lex_name, e=entry, pp=parent_popup: self._perform_add_entry(l, e, pp))
            grid.add_widget(btn)

        scroll.add_widget(grid)
        layout.add_widget(scroll)

        cancel_btn = RoundButton(text="取消", size_hint_y=None, height=button_height, bg_color=(0.8, 0.3, 0.3, 1))
        layout.add_widget(cancel_btn)

        # --- Popup Creation ---
        self.lexicon_popup = Popup(
            title='', # No title bar title
            content=layout,
            size_hint=(0.7, 0.6),
            separator_height=0 # Remove title bar visually
        )
        cancel_btn.bind(on_press=self.lexicon_popup.dismiss)
        self.lexicon_popup.open()

    def _perform_add_entry(self, lexicon_name, entry, parent_popup):
        # --- 使用 self.lexicon ---
        success, message = self.lexicon.add_entry_to_lexicon(entry, lexicon_name)

        if self.lexicon_popup:
            self.lexicon_popup.dismiss()
            self.lexicon_popup = None

        show_message(message, title='添加结果')

        # Optionally close the parent (details) popup if add was successful
        # if success and parent_popup:
        #     parent_popup.dismiss()

    # get_available_lexicons 不再需要，因为 Lexicon 实例有 get_lexicon_list 方法
    # def get_available_lexicons(self):
    #     """Gets list of lexicon names, excluding 'default' and 'defaults'."""
    #     lex_dir = os.path.join(os.path.dirname(__file__), '..', 'lexicons') # Path relative to this file
    #     if not os.path.isdir(lex_dir):
    #         return []
    #     try:
    #         all_files = [f for f in os.listdir(lex_dir) if f.endswith('.json')]
    #         excluded = {'default.json', 'defaults.json'}
    #         return sorted([os.path.splitext(f)[0] for f in all_files if f not in excluded])
    #     except FileNotFoundError:
    #         return []

    # _format_result is likely unused if results always go to popup
    # def _format_result(self, result): ...