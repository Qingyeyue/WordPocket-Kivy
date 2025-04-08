# screens/lexicon_screen.py
import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock

# 不再需要导入 core.Lexicon
# from core.lexicon import Lexicon
from core.data import Data
from ui_elements.buttons import RoundButton
from ui_elements.labels import create_wrapped_label
from utils.popups import show_message, show_confirmation

# 常量定义
BUTTON_HEIGHT_NORMAL = 80
BUTTON_HEIGHT_LARGE = 100
EVEN_COLOR = (0.275, 0.510, 0.706, 1)
ODD_COLOR = (0.4, 0.65, 0.8, 1)
DELETE_COLOR = (0.9, 0.2, 0.2, 1)
CONFIRM_COLOR = (0.2, 0.8, 0.2, 1)

class LexiconScreen(BoxLayout):
    def __init__(self, return_to_main, lexicon_instance, data_instance, **kwargs):
        super(LexiconScreen, self).__init__(**kwargs)
        self.return_to_main = return_to_main
        self.orientation = 'vertical'
        self.spacing = 5
        self.padding = 10

        # 2. 存储共享实例
        self.lexicon = lexicon_instance
        self.data = data_instance
        # 3. 确保没有在这里创建 self.lexicon = Lexicon() 或 self.data = Data()

        # 状态变量
        self.lexicons_available = []  # 将在 show_lexicon_list_view 中填充
        self.current_lexicon_name = None
        self.all_entries_in_view = []
        self.sort_option = ('alphabetical', False)  # 默认按中文正序 (来自 Data.sort_entries)

        # 分页状态
        self.current_page = 0
        self.results_per_page = 30
        self.total_pages = 0

        # UI 引用
        self.grid_layout = None
        self.scroll_view = None
        self.page_label = None
        self.prev_btn = None
        self.next_btn = None
        self.footer = None  # 页脚容器

        # 启动流程
        self.show_lexicon_list_view()

    def _create_main_layout(self):
        """Creates the basic structure with header, scrollview, and footer."""
        self.clear_widgets()

        # Header (e.g., for title or actions) - Optional
        # header = BoxLayout(size_hint_y=None, height=50)
        # self.add_widget(header)

        # Scroll View for content
        self.scroll_view = ScrollView(size_hint=(1, 1)) # Takes most space
        self.grid_layout = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))
        self.scroll_view.add_widget(self.grid_layout)
        self.add_widget(self.scroll_view)

        # Footer (e.g., for main action buttons)
        self.footer = BoxLayout(size_hint_y=None, height=BUTTON_HEIGHT_LARGE, spacing=10)
        self.add_widget(self.footer)

    def show_lexicon_list_view(self):
        """Displays the list of available lexicons."""
        self._create_main_layout()
        self.current_lexicon_name = None

        # --- 使用 self.lexicon 获取列表 ---
        self.lexicons_available = self.lexicon.get_lexicon_list()

        if not self.lexicons_available:
            self.grid_layout.add_widget(Label(text="无自定义词库", size_hint_y=None, height=100))
        else:
            for index, lexicon_name in enumerate(self.lexicons_available):
                bg_color = EVEN_COLOR if index % 2 == 0 else ODD_COLOR
                button = RoundButton(
                    text=lexicon_name,
                    size_hint_y=None,
                    height=BUTTON_HEIGHT_NORMAL,
                    bg_color=bg_color
                )
                button.lexicon_name = lexicon_name
                # show_lexicon_entries_view 不需要修改
                button.bind(on_press=self.show_lexicon_entries_view)
                self.grid_layout.add_widget(button)

        # 页脚按钮
        self.footer.clear_widgets()
        new_lex_button = RoundButton(text='新建词库')
        filter_lex_button = RoundButton(text='筛选词库') # Keep filter consolidate?
        return_main_button = RoundButton(text='返回主页', bg_color=(0.6, 0.6, 0.6, 1))

        new_lex_button.bind(on_press=self.show_new_lexicon_popup)
        filter_lex_button.bind(on_press=self.show_filter_consolidate_popup) # Link to filter func
        return_main_button.bind(on_press=self.return_to_main)

        self.footer.add_widget(new_lex_button)
        self.footer.add_widget(filter_lex_button)
        self.footer.add_widget(return_main_button)

    def show_lexicon_entries_view(self, instance):
        """Displays entries within a selected lexicon with pagination."""
        self.current_lexicon_name = instance.lexicon_name
        self._create_main_layout() # Rebuild layout for entry view

        # 添加分页控件
        pagination_height = 60
        pagination = BoxLayout(size_hint_y=None, height=pagination_height, spacing=5)
        self.prev_btn = RoundButton(text="<", size_hint_x=0.2, disabled=True)
        self.page_label = Label(text="1 / 1", size_hint_x=0.6)
        self.next_btn = RoundButton(text=">", size_hint_x=0.2, disabled=True)
        self.prev_btn.bind(on_press=lambda x: self._change_entry_page(-1))
        self.next_btn.bind(on_press=lambda x: self._change_entry_page(1))
        pagination.add_widget(self.prev_btn)
        pagination.add_widget(self.page_label)
        pagination.add_widget(self.next_btn)
        # Insert pagination before the scroll view
        self.add_widget(pagination, index=len(self.children)-1)

        # --- 使用 self.lexicon 和 self.data 加载和排序 ---
        self._load_and_sort_entries()  # 这个方法内部会使用 self.lexicon 和 self.data
        self._display_current_entry_page()  # 这个方法显示 self.all_entries_in_view

        # 页脚按钮
        self.footer.clear_widgets()
        rename_button = RoundButton(text='重命名')
        delete_lex_button = RoundButton(text='删除词库', bg_color=DELETE_COLOR)
        delete_entries_button = RoundButton(text='删条目')
        sort_button = RoundButton(text='排序')
        back_button = RoundButton(text='返回列表', bg_color=(0.6, 0.6, 0.6, 1))

        rename_button.bind(on_press=self.show_rename_lexicon_popup)
        delete_lex_button.bind(on_press=self.show_delete_lexicon_popup)
        delete_entries_button.bind(on_press=self.show_delete_entries_popup)
        sort_button.bind(on_press=self.show_sort_options_popup)
        back_button.bind(on_press=lambda btn: self.show_lexicon_list_view())

        self.footer.add_widget(rename_button)
        self.footer.add_widget(delete_lex_button)
        self.footer.add_widget(delete_entries_button)
        self.footer.add_widget(sort_button)
        self.footer.add_widget(back_button)

    def _load_and_sort_entries(self):
        """Loads entries for the current lexicon and applies sorting."""
        try:
            # --- 使用 self.lexicon 获取条目 ---
            all_entries = self.lexicon.get_lexicon_entries(self.current_lexicon_name)
            # --- 使用 self.data 排序 (静态方法) ---
            self.all_entries_in_view = Data.sort_entries(all_entries, *self.sort_option)
            # 或者如果 sort_entries 需要实例: self.data.sort_entries(...)
        except Exception as e:
            self.all_entries_in_view = []
            show_message(f"加载或排序词库 '{self.current_lexicon_name}' 时出错:\n{e}", title="错误")

        # 更新分页状态
        self.current_page = 0
        self.total_pages = (len(self.all_entries_in_view) + self.results_per_page - 1) // self.results_per_page
        self.total_pages = max(1, self.total_pages) # Ensure at least 1 page

    def _display_current_entry_page(self):
        """Clears and repopulates the grid with the current page's entries."""
        self.grid_layout.clear_widgets()
        start = self.current_page * self.results_per_page
        end = start + self.results_per_page
        current_entries_page = self.all_entries_in_view[start:end]

        if not current_entries_page:
            self.grid_layout.add_widget(Label(text="此词库为空", size_hint_y=None, height=100))
        else:
            for index, entry in enumerate(current_entries_page):
                bg_color = EVEN_COLOR if index % 2 == 0 else ODD_COLOR
                # Use a simpler format for the list button
                btn_text = f"中: {entry.get('chinese', '')[:15]} | 英: {entry.get('english', '')[:20]}"
                if len(btn_text) > 38: btn_text = btn_text[:35] + "..."

                button = RoundButton(
                    text=btn_text,
                    size_hint_y=None,
                    height=BUTTON_HEIGHT_NORMAL,
                    bg_color=bg_color,
                    halign='left', padding=(10, 5) # Align left
                )
                button.entry_data = entry # Store data
                # Link to the *specific* detail popup for this screen
                button.bind(on_press=lambda btn, ent=entry: self.show_lexicon_entry_details_popup(ent))
                self.grid_layout.add_widget(button)

        self._update_entry_pagination_controls()
        if self.scroll_view:
             self.scroll_view.scroll_y = 1 # Scroll to top

    def _update_entry_pagination_controls(self):
        """Updates pagination buttons based on current page and total pages."""
        if self.page_label:
            self.page_label.text = f"{self.current_page + 1} / {self.total_pages}"
        if self.prev_btn:
            self.prev_btn.disabled = self.current_page <= 0
        if self.next_btn:
            self.next_btn.disabled = self.current_page >= self.total_pages - 1

    def _change_entry_page(self, delta):
        """Changes the current page and redisplays."""
        new_page = self.current_page + delta
        if 0 <= new_page < self.total_pages:
            self.current_page = new_page
            self._display_current_entry_page()

    # --- Action Popups & Handlers ---

    def show_new_lexicon_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        input_name = TextInput(hint_text='输入新词库名称', multiline=False, size_hint_y=None, height=50)
        content.add_widget(Label(text="新词库名称:", size_hint_y=None, height=30))
        content.add_widget(input_name)
        content.add_widget(BoxLayout(size_hint_y=1)) # Spacer

        button_layout = BoxLayout(size_hint_y=None, height=BUTTON_HEIGHT_NORMAL, spacing=10)
        create_button = RoundButton(text='创建', bg_color=CONFIRM_COLOR)
        cancel_button = RoundButton(text='取消')
        button_layout.add_widget(create_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)

        popup = Popup(title='新建词库', content=content, size_hint=(0.8, 0.5), auto_dismiss=False)

        def create_action():
            name = input_name.text.strip()
            if not name:
                show_message("名称不能为空")
                return
            if name in self.lexicon.get_lexicon_list() or name == 'defaults':
                show_message(f"名称 '{name}' 已存在或无效")
            elif self.lexicon.create_lexicon(name):
                show_message(f"词库 '{name}' 创建成功")
                self.lexicons.append(name) # Update local list
                self.show_lexicon_list_view() # Refresh view
                popup.dismiss()
            else:
                show_message("创建词库失败，请检查权限或文件名。")

        create_button.bind(on_press=lambda btn: create_action())
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()

    def show_rename_lexicon_popup(self, instance):
        if not self.current_lexicon_name: return

        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        input_name = TextInput(hint_text='输入新名称', text=self.current_lexicon_name, multiline=False, size_hint_y=None, height=50)
        content.add_widget(Label(text="新名称:", size_hint_y=None, height=30))
        content.add_widget(input_name)
        content.add_widget(BoxLayout(size_hint_y=1)) # Spacer

        button_layout = BoxLayout(size_hint_y=None, height=BUTTON_HEIGHT_NORMAL, spacing=10)
        rename_button = RoundButton(text='重命名', bg_color=CONFIRM_COLOR)
        cancel_button = RoundButton(text='取消')
        button_layout.add_widget(rename_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)

        popup = Popup(title='重命名词库', content=content, size_hint=(0.8, 0.5), auto_dismiss=False)

        def rename_action():
            new_name = input_name.text.strip()
            old_name = self.current_lexicon_name
            if not new_name:
                show_message("名称不能为空")
                return
            if new_name == old_name:
                 popup.dismiss() # No change needed
                 return
            if new_name in self.lexicon.get_lexicon_list() or new_name == 'defaults':
                show_message(f"名称 '{new_name}' 已存在或无效")
            elif self.lexicon.rename_lexicon(old_name, new_name):
                show_message(f"词库已重命名为 '{new_name}'")
                # 更新当前名称并刷新视图
                self.current_lexicon_name = new_name
                # _load_and_sort_entries 会重新加载，所以直接显示页面
                self._load_and_sort_entries()
                self._display_current_entry_page()
                # 手动更新一下 footer 下的按钮文本或状态可能需要
                popup.dismiss()
            else:
                show_message("重命名失败。")

        rename_button.bind(on_press=lambda btn: rename_action())
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()

    def show_delete_lexicon_popup(self, instance):
        if not self.current_lexicon_name: return
        show_confirmation(
            f"确定要永久删除词库\n'{self.current_lexicon_name}' 吗？\n此操作无法撤销。",
            on_confirm=self.delete_current_lexicon,
            title='确认删除词库'
        )

    def delete_current_lexicon(self):
        if not self.current_lexicon_name: return
        old_name = self.current_lexicon_name
        if self.lexicon.delete_lexicon(old_name):  # 使用实例方法
            show_message("删除成功")
            self.current_lexicon_name = None
            self.show_lexicon_list_view()  # 返回列表视图
        else:
            show_message(f"删除词库 '{old_name}' 失败")

    def show_delete_entries_popup(self, instance):
        entries_for_selection = self.all_entries_in_view  # 假设已加载所有
        if not entries_for_selection:
            show_message("当前词库没有条目可删除。")
            return

        content = BoxLayout(orientation='vertical', spacing=5)
        content.add_widget(Label(text="选择要删除的条目:", size_hint_y=None, height=40))

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, size_hint_y=None, spacing=5)
        grid.bind(minimum_height=grid.setter('height'))

        selected_entries_for_deletion = [] # Track selections

        def toggle_selection(checkbox, value, entry):
            if value:
                selected_entries_for_deletion.append(entry)
            else:
                if entry in selected_entries_for_deletion:
                    selected_entries_for_deletion.remove(entry)

        # Display ALL entries for selection, not just current page
        for entry in self.all_entries_in_view:
             entry_layout = BoxLayout(size_hint_y=None, height=50)
             # Shorten text for display
             text = f"中:{entry.get('chinese','')[:10]} 英:{entry.get('english','')[:15]}"
             entry_label = Label(text=text, size_hint_x=0.8, halign='left', valign='middle', text_size=(None,50))
             entry_label.bind(width=lambda *x: entry_label.setter('text_size')(entry_label, (entry_label.width, None)))

             entry_checkbox = CheckBox(size_hint_x=0.2)
             entry_checkbox.bind(active=lambda cb, val, e=entry: toggle_selection(cb, val, e))
             entry_layout.add_widget(entry_label)
             entry_layout.add_widget(entry_checkbox)
             grid.add_widget(entry_layout)

        scroll.add_widget(grid)
        content.add_widget(scroll)

        button_layout = BoxLayout(size_hint_y=None, height=BUTTON_HEIGHT_NORMAL, spacing=10)
        delete_button = RoundButton(text='删除选中', bg_color=DELETE_COLOR)
        cancel_button = RoundButton(text='取消')
        button_layout.add_widget(delete_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)

        popup = Popup(title='删除条目', content=content, size_hint=(0.9, 0.85), auto_dismiss=False)

        def confirm_delete():
            if not selected_entries_for_deletion:
                show_message("未选择任何条目。")
                return

            count = len(selected_entries_for_deletion)
            show_confirmation(
                f"确定要从词库 '{self.current_lexicon_name}'\n中删除选中的 {count} 个条目吗？",
                on_confirm=lambda: self.delete_selected_entries_action(selected_entries_for_deletion, popup),
                title='确认删除条目'
            )

        delete_button.bind(on_press=lambda btn: confirm_delete())
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()

    def delete_selected_entries_action(self, entries_to_delete, delete_popup):
        if not self.current_lexicon_name or not entries_to_delete:
            return

        success_count = 0
        fail_count = 0
        # --- 使用 self.lexicon ---
        for entry in entries_to_delete:
            # 使用实例方法
            success, _ = self.lexicon.remove_entry_from_lexicon(entry, self.current_lexicon_name)
            if success:
                success_count += 1
            else:
                fail_count += 1

        delete_popup.dismiss()

        show_message(f"成功删除 {success_count} 个条目。\n失败 {fail_count} 个。", title="删除结果")

        # 刷新视图
        self._load_and_sort_entries()
        self._display_current_entry_page()

    def show_sort_options_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text="选择排序方式", size_hint_y=None, height=40))

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, size_hint_y=None, spacing=10)
        grid.bind(minimum_height=grid.setter('height'))

        sort_options = self.data.get_sort_options()

        for label, sort_key, reverse in sort_options:
            option_tuple = (sort_key, reverse)
            # Indicate current sort
            is_current = self.sort_option == option_tuple
            display_text = f"{label}{' (当前)' if is_current else ''}"

            button = RoundButton(
                text=display_text,
                size_hint_y=None,
                height=BUTTON_HEIGHT_NORMAL,
                bg_color=CONFIRM_COLOR if is_current else (0.5, 0.5, 0.5, 1)
                )
            button.sort_option = option_tuple # Store the option data
            button.bind(on_press=lambda btn, opt=option_tuple: self.set_sort_option_and_refresh(opt, popup))
            grid.add_widget(button)

        scroll.add_widget(grid)
        content.add_widget(scroll)

        close_button = RoundButton(text='关闭', size_hint_y=None, height=BUTTON_HEIGHT_NORMAL)
        content.add_widget(close_button)

        popup = Popup(title='排序选项', content=content, size_hint=(0.8, 0.7), auto_dismiss=False)
        close_button.bind(on_press=popup.dismiss)
        popup.open()

    def set_sort_option_and_refresh(self, sort_option, sort_popup):
        self.sort_option = sort_option
        sort_popup.dismiss()
        # 重新加载、排序、显示
        self._load_and_sort_entries()
        self._display_current_entry_page()

    def show_lexicon_entry_details_popup(self, entry):
        # --- 可选：这里是否需要更新查询次数？如果需要，使用 self.lexicon ---
        # self.lexicon.update_entry_in_defaults(entry) # 如果需要更新查询数

        # --- 布局，显示 entry 内容 ---
        main_layout = BoxLayout(orientation='vertical', spacing=5, padding=10)

        scroll_content = ScrollView(size_hint=(1, 0.8))
        content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content_box.bind(minimum_height=content_box.setter('height'))
        label_font_size = 20
        content_box.add_widget(create_wrapped_label(f"中文: {entry.get('chinese', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"英文: {entry.get('english', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"备注: {entry.get('note', '')}", font_size=label_font_size))
        content_box.add_widget(create_wrapped_label(f"查:{entry.get('inquiry',0)} 记:{entry.get('memory',0)} 错:{entry.get('mistake',0)}", font_size=label_font_size - 4))
        scroll_content.add_widget(content_box)
        main_layout.add_widget(scroll_content)

        # Action Buttons for Lexicon context
        buttons_layout = BoxLayout(size_hint=(1, None), height=BUTTON_HEIGHT_NORMAL, spacing=10)
        # Add "Add to Other Lexicon" button maybe?
        remove_btn = RoundButton(text='从此词库移除', bg_color=DELETE_COLOR)
        close_btn = RoundButton(text='关闭')

        buttons_layout.add_widget(remove_btn)
        buttons_layout.add_widget(close_btn)
        main_layout.add_widget(buttons_layout)

        popup = Popup(title='条目详情', content=main_layout, size_hint=(0.85, 0.7), auto_dismiss=False)

        # --- confirm_remove... 会使用 self.lexicon ---
        remove_btn.bind(on_press=lambda btn: self.confirm_remove_entry_from_current_lexicon(entry, popup))
        close_btn.bind(on_press=popup.dismiss)

        popup.open()

    def confirm_remove_entry_from_current_lexicon(self, entry, detail_popup):
        if not self.current_lexicon_name: return
        show_confirmation(
             f"确定要从词库 '{self.current_lexicon_name}'\n移除条目:\n'{entry.get('chinese', '')[:20]}...'?",
             on_confirm=lambda: self.remove_entry_action(entry, detail_popup),
             title='确认移除条目'
        )

    def remove_entry_action(self, entry, detail_popup):
         if not self.current_lexicon_name: return
         # --- 使用 self.lexicon ---
         success, _ = self.lexicon.remove_entry_from_lexicon(entry, self.current_lexicon_name)  # 实例方法
         detail_popup.dismiss()
         if success:
             show_message("条目已移除")
             # 刷新视图
             self._load_and_sort_entries()
             self._display_current_entry_page()
         else:
             show_message("移除条目失败")

    # --- 筛选巩固词逻辑 ---
    def show_filter_consolidate_popup(self, instance):
         # Similar to show_sort_options_popup, but lists lexicons
         content = BoxLayout(orientation='vertical', spacing=10, padding=10)
         content.add_widget(Label(text="选择要筛选'巩固词'的词库", size_hint_y=None, height=40))

         scroll = ScrollView(size_hint=(1, 1))
         grid = GridLayout(cols=1, size_hint_y=None, spacing=10)
         grid.bind(minimum_height=grid.setter('height'))

         available_lexicons = self.lexicon.get_lexicon_list()

         if not available_lexicons:
             grid.add_widget(Label(text="无自定义词库可筛选"))
         else:
             for lexicon_name in available_lexicons:
                 button = RoundButton(
                     text=lexicon_name,
                     size_hint_y=None,
                     height=BUTTON_HEIGHT_NORMAL
                 )
                 button.lexicon_name = lexicon_name
                 button.bind(on_press=lambda btn, ln=lexicon_name: self.execute_filter_consolidate(ln, popup))
                 grid.add_widget(button)

         scroll.add_widget(grid)
         content.add_widget(scroll)

         close_button = RoundButton(text='取消', size_hint_y=None, height=BUTTON_HEIGHT_NORMAL)
         content.add_widget(close_button)

         popup = Popup(title="筛选巩固词", content=content, size_hint=(0.8, 0.7), auto_dismiss=False)
         close_button.bind(on_press=popup.dismiss)
         popup.open()

    def execute_filter_consolidate(self, lexicon_name, filter_popup):
        filter_popup.dismiss() # Close the selection popup

        try:
            # --- 使用 self.lexicon 获取条目 ---
            entries = self.lexicon.get_lexicon_entries(lexicon_name)
            if not entries:
                show_message(f"词库 '{lexicon_name}' 为空或加载失败。", title="筛选结果")
                return

            # --- 使用 self.data 筛选 (静态方法) ---
            filtered_entries = Data.filter_entries(entries, 'consolidate')

            if not filtered_entries:
                show_message(f"词库 '{lexicon_name}' 中\n没有找到'巩固'类型的词条。", title="筛选结果")
                return

            # --- 使用 self.lexicon 获取索引 (实例方法) ---
            # get_entry_indices 已经帮我们处理了从 entry 到 index 的映射
            filtered_indices = self.lexicon.get_entry_indices(filtered_entries)

            # --- 这里不再需要之前的 english_to_index 字典查找了 ---
            # --- 删除或注释掉以下错误行：---
            # english_to_index = {v['english']: k for k, v in self.lexicon.defaults.items() if isinstance(k, int)}
            # filtered_indices = []
            # for entry in filtered_entries:
            #     idx = english_to_index.get(entry.get('english'))
            #     if idx is not None:
            #         filtered_indices.append(idx)
            # --- 以上错误代码已由 self.lexicon.get_entry_indices(filtered_entries) 替代 ---

            if not filtered_indices:
                # 这通常意味着 get_entry_indices 内部未能找到索引，应该检查 find_entry_index
                show_message("无法将筛选出的词条映射回索引。\n请检查主词库数据。", title="内部错误")
                return

            # 创建新词库名
            new_lexicon_name = f"{lexicon_name}_consolidate"

            # --- 使用 self.lexicon 检查列表 ---
            if new_lexicon_name in self.lexicon.get_lexicon_list():
                show_confirmation(
                     f"词库 '{new_lexicon_name}' 已存在。\n是否覆盖它？",
                     on_confirm=lambda: self.save_filtered_lexicon(new_lexicon_name, filtered_indices),
                     title="确认覆盖"
                 )
            else:
                 self.save_filtered_lexicon(new_lexicon_name, filtered_indices)


        except Exception as e:
            # --- 捕获异常时，传递错误的字符串表示给 show_message ---
            print(f"筛选时发生未预料的错误: {e}")  # 在控制台打印详细错误
            import traceback
            traceback.print_exc()  # 打印完整的堆栈跟踪，方便调试
            show_message(f"筛选时发生错误:\n{str(e)}", title="筛选错误")  # 使用 str(e) 获取错误信息字符串

    def save_filtered_lexicon(self, name, indices):
        # --- 使用 self.lexicon 保存 (实例方法) ---
        if self.lexicon.save_lexicon(name, indices):
            show_message(f"已创建新词库:\n'{name}'\n包含 {len(indices)} 个巩固词条。", title="筛选成功")
            # 刷新主列表视图
            self.show_lexicon_list_view()
        else:
            show_message(f"保存新词库 '{name}' 失败。", title="保存错误")