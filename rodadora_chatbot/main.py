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

from threading import Thread
from queue import Queue
from chatbot.main import Chatbot


class Chat(MDWidget):
    messages = ListProperty([])

    def __init__(self):
        super().__init__()
        self.requests = Queue()

        def chatter():
            chatbot = Chatbot()

            while True:
                item = self.requests.get()
                if item is None:
                    break

                response = chatbot.chat(item)
                self.receive(response)

        self.background_thread = Thread(target=chatter)
        self.background_thread.start()

    def __del__(self):
        self.requests.put(None)
        self.background_thread.join()

    def send(self, text):
        if not text:
            return

        self.messages.append({"text": text, "sent": True, "pos_hint": {"right": 1}})

        # scroll to bottom
        rv = self.ids.chat_rv
        box = self.ids.chat_box
        if rv.height < box.height:
            Animation.cancel_all(rv, "scroll_y")
            Animation(scroll_y=0, t="out_quad", d=0.5).start(rv)

        self.requests.put(text)

    def receive(self, text):
        self.messages.append({"text": text, "sent": False})

    def record_message(self):
        print("TODO: iniciar grabación en segundo thread")


class ChatApp(MDApp):
    def on_stop(self):
        self.chat.__del__()

    def build(self):
        self.title = "La Rodadora"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "LightBlue"
        self.chat = Chat()
        return self.chat


if __name__ == "__main__":
    Window.size = (1000, 700)
    ChatApp().run()
