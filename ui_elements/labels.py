from kivy.uix.label import Label
from kivy.core.window import Window

def create_wrapped_label(text, font_size=None, **kwargs):
    """Creates a Label that wraps text within the window width."""
    if 'halign' in kwargs:
        del kwargs['halign']
    if 'valign' in kwargs:
        del kwargs['valign']

    label = Label(
        text=text,
        size_hint_y=None,
        halign='center',
        valign='top',
        markup=True,
        **kwargs  # Allow passing other Label properties
    )

    # Set initial text_size based on current window width if available
    label.text_size = (Window.width - 40, None) # Adjust padding as needed

    if font_size:
        label.font_size = font_size

    # Adjust text_size and height automatically
    def update_text_size(instance, width):
        instance.text_size = (width - 40, None) # Keep consistent padding

    def update_height(instance, texture_size):
        instance.height = texture_size[1]

    label.bind(width=update_text_size, texture_size=update_height)

    # Trigger initial height calculation
    label.texture_update()
    label.height = label.texture_size[1]

    return label