# main.py
import os
# Kivy setup
from kivy.app import App
from kivy.core.text import LabelBase
# from kivy.core.window import Window
# from kivy.utils import platform

# --- 字体注册 ---
font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'msyh.ttc')
LabelBase.register(name='Roboto', fn_regular=font_path)


# --- 导入核心逻辑和主屏幕 ---
from core.lexicon import Lexicon
from core.data import Data
from screens.main_screen import MainScreen

class WordApp(App):
    def build(self):
        """构建主界面并初始化共享的数据实例"""
        # --- 创建共享实例 ---
        try:
            self.shared_lexicon = Lexicon()  # Lexicon 初始化时会加载 defaults
        except FileNotFoundError as e:
             print(f"严重错误: 初始化 Lexicon 时出错 - {e}")
             # 可能需要显示错误弹窗并退出
             # self.show_error_popup_and_exit(f"无法找到 Lexicon 目录或文件: {e}")
             return None # 返回 None 会导致应用退出

        # 检查 Lexicon 是否成功加载了 defaults
        if not self.shared_lexicon.defaults:
             print("严重错误: Lexicon 未能加载 defaults.json。应用可能无法正常工作。")
             # self.show_error_popup_and_exit("无法加载核心词库文件 (defaults.json)。")
             return None

        # 创建 Data 实例，并传入共享的 Lexicon 实例
        self.shared_data = Data(self.shared_lexicon)

        # --- 传递共享实例给主屏幕 ---
        main_screen = MainScreen(
            lexicon_instance=self.shared_lexicon,
            data_instance=self.shared_data,
            app_instance=self
        )
        return main_screen

    # (可选) 添加一个错误弹窗方法
    # def show_error_popup_and_exit(self, message):
    #    from kivy.uix.popup import Popup
    #    from kivy.uix.label import Label
    #    from kivy.uix.boxlayout import BoxLayout
    #    from kivy.uix.button import Button
    #    layout = BoxLayout(orientation='vertical')
    #    layout.add_widget(Label(text=message))
    #    btn = Button(text='确定并退出', size_hint_y=None, height=50)
    #    btn.bind(on_press=self.stop) # self.stop() 会关闭应用
    #    layout.add_widget(btn)
    #    popup = Popup(title='启动错误', content=layout, size_hint=(0.8, 0.4), auto_dismiss=False)
    #    popup.open()

# --- Entry Point ---
if __name__ == '__main__':
    WordApp().run()