# screens/main_screen.py
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation

# Use relative imports for sibling modules (screens)
from .query_screen import QueryScreen
from .recite_screen import ReciteScreen
from .lexicon_screen import LexiconScreen

# Import RoundButton from its new location
from ui_elements.buttons import RoundButton

class MainScreen(BoxLayout):
    def __init__(self, lexicon_instance, data_instance, app_instance=None, **kwargs): # Pass app instance if needed later
        super(MainScreen, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.app = app_instance # 可选

        # 2. 存储共享实例
        self.lexicon = lexicon_instance
        self.data = data_instance

        # Button Creation (rest remains the same)
        self.query_button = RoundButton(text='查询', font_size=500, color=(1, 1, 1, 1), bg_color=(0.529, 0.808, 0.922, 1), animation_duration=0.1, enable_ripple=True, ripple_color=(1, 1, 1, 0.3))
        self.query_button.bind(on_press=self.show_query_screen)
        self.add_widget(self.query_button)

        self.recite_button = RoundButton(text='记忆', font_size=500, color=(1, 1, 1, 1), bg_color=(0.275, 0.510, 0.706, 1), animation_duration=0.1, enable_ripple=True, ripple_color=(1, 1, 1, 0.3))
        self.recite_button.bind(on_press=self.show_recite_screen)
        self.add_widget(self.recite_button)

        self.lexicon_button = RoundButton(text='词库', font_size=500, color=(1, 1, 1, 1), bg_color=(0.118, 0.216, 0.600, 1), animation_duration=0.1, enable_ripple=True, ripple_color=(1, 1, 1, 0.3))
        self.lexicon_button.bind(on_press=self.show_lexicon_screen)
        self.add_widget(self.lexicon_button)

        self._add_main_buttons()  # 调用添加按钮的方法

    # 动画辅助方法 (不变)
    def _create_switch_animation(self, instance, switch_method):
        anim = (
            Animation(scale=0.95, duration=0.1)
            + Animation(scale=1, duration=0.1)
        )
        anim.bind(on_complete=lambda *_: switch_method())
        anim.start(instance)
        # Optional: self.app.start_animation(instance, anim) if using App animation tracking

    def show_query_screen(self, instance):
        self._create_switch_animation(instance, self._switch_to_query)

    def show_recite_screen(self, instance):
        self._create_switch_animation(instance, self._switch_to_recite)

    def show_lexicon_screen(self, instance):
        self._create_switch_animation(instance, self._switch_to_lexicon)

    # --- Switching Methods ---
    # These now instantiate classes from other modules

    # 修改切换屏幕的方法以传递实例
    def _switch_to_query(self):
        self.clear_widgets()
        # Pass the callback to return to this screen's logic
        self.add_widget(QueryScreen(
            return_to_main=self.show_main_screen,  # 回调函数
            lexicon_instance=self.lexicon,  # 传递共享实例
            data_instance=self.data  # 传递共享实例
        ))

    def _switch_to_recite(self):
        self.clear_widgets()
        self.add_widget(ReciteScreen(
            return_to_main=self.show_main_screen,
            lexicon_instance=self.lexicon,
            data_instance=self.data
        ))

    def _switch_to_lexicon(self):
        self.clear_widgets()
        self.add_widget(LexiconScreen(
            return_to_main=self.show_main_screen,
            lexicon_instance=self.lexicon,
            data_instance=self.data
        ))

    # --- Return Logic ---
    # 返回主屏幕的逻辑 (确保 _add_main_buttons 被调用)
    def show_main_screen(self, instance=None):
        if instance:
             Animation.cancel_all(instance)
             instance.scale = 1
        self.clear_widgets()
        self._add_main_buttons()  # 重新构建按钮

    def _add_main_buttons(self):
        self.clear_widgets()

        self.query_button = RoundButton(text='查询', font_size=500, color=(1, 1, 1, 1), bg_color=(0.529, 0.808, 0.922, 1), animation_duration=0.1, enable_ripple=True, ripple_color=(1, 1, 1, 0.3))
        self.query_button.bind(on_press=self.show_query_screen)
        self.add_widget(self.query_button)

        self.recite_button = RoundButton(text='记忆', font_size=500, color=(1, 1, 1, 1), bg_color=(0.275, 0.510, 0.706, 1), animation_duration=0.1, enable_ripple=True, ripple_color=(1, 1, 1, 0.3))
        self.recite_button.bind(on_press=self.show_recite_screen)
        self.add_widget(self.recite_button)

        self.lexicon_button = RoundButton(text='词库', font_size=500, color=(1, 1, 1, 1), bg_color=(0.118, 0.216, 0.600, 1), animation_duration=0.1, enable_ripple=True, ripple_color=(1, 1, 1, 0.3))
        self.lexicon_button.bind(on_press=self.show_lexicon_screen)
        self.add_widget(self.lexicon_button)