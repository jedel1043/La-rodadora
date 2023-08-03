from kivy.graphics.svg import Svg
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import StringProperty, ListProperty
from kivy.core.window import Window
from kivy.animation import Animation

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.widget import MDWidget

import components

class Chat(MDWidget):
    messages = ListProperty([])

    def send(self, text):
        if not text:
            return

        self.messages.append(
            {"text": text, "sent": True, "pos_hint": {"right": 1}}
        )

        # scroll to bottom
        rv = self.ids.chat_rv
        box = self.ids.chat_box
        if rv.height < box.height:
            Animation.cancel_all(rv, "scroll_y")
            Animation(scroll_y=0, t="out_quad", d=0.5).start(rv)
        self.receive(text=text)

    def receive(self, text):
        self.messages.append(
            {"text": text, "sent": False}
        )


class ChatApp(MDApp):
    def build(self):
        self.title = "La Rodadora"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "LightBlue"
        return Chat()

if __name__ == "__main__":
    Window.size = (1000, 700)
    ChatApp().run()
