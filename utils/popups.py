# utils/popups.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from ui_elements.buttons import RoundButton # Adjust import path if needed

def show_message(message, title='提示', size_hint=(0.8, 0.4)):
    """Displays a simple message popup."""
    content = BoxLayout(orientation='vertical', spacing=10, padding=10)
    content.add_widget(Label(text=str(message), size_hint_y=None, height=100)) # Give label some space

    close_button = RoundButton(text='关闭', size_hint_y=None, height=100) # Smaller button for simple message
    popup = Popup(title=title, content=content, size_hint=size_hint, auto_dismiss=False)
    close_button.bind(on_press=popup.dismiss)
    content.add_widget(close_button)

    popup.open()

def show_confirmation(message, on_confirm, title='确认操作', size_hint=(0.8, 0.5)):
    """Displays a confirmation popup with Confirm and Cancel buttons."""
    content = BoxLayout(orientation='vertical', spacing=10, padding=10)
    content.add_widget(Label(text=message, size_hint_y=1)) # Let label fill space

    button_layout = BoxLayout(size_hint_y=None, height=100, spacing=10) # Button row

    confirm_button = RoundButton(text='确认')
    cancel_button = RoundButton(text='取消', bg_color=(0.8, 0.3, 0.3, 1)) # Indicate cancel/destructive

    popup = Popup(title=title, content=content, size_hint=size_hint, auto_dismiss=False)

    def confirm_action(instance):
        popup.dismiss()
        if on_confirm:
            on_confirm()

    confirm_button.bind(on_press=confirm_action)
    cancel_button.bind(on_press=popup.dismiss)

    button_layout.add_widget(confirm_button)
    button_layout.add_widget(cancel_button)
    content.add_widget(button_layout)

    popup.open()

# Add other common popup patterns here if needed (e.g., lexicon selection)
# Note: show_lexicon_selection and show_entry_details are complex and might
# be better kept within the screens that use them or heavily customized here.