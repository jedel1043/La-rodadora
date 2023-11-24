from kivy.lang import Builder
from kivy.properties import ColorProperty, StringProperty
from kivy.uix.label import Label
from kivymd.uix.label import MDLabel

from components.adaptive_widget import AdaptiveWidget

Builder.load_string(
    """
<PLabel>
    font_name: 'Roboto'
    color:
        self.text_color if self.text_color \
        else app.theme_cls.text_color
"""
)


class PLabel(AdaptiveWidget, MDLabel):
    text_color = ColorProperty(None)