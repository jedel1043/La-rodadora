from kivy.graphics.svg import Svg
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import StringProperty, ListProperty
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.lang import Builder
from kivy.app import async_runTouchApp

from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.widget import MDWidget
from kivymd.uix.button import MDIconButton
import trio
import torch
from langdetect import detect

import components
from tasks import chatbot, record, tts

class Chat(MDWidget):
    messages = ListProperty([])

    def __init__(self, sender, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mute: bool = False
        self.sender: trio.MemorySendChannel = sender

    def send_event(self, typ, value):
        while True:
            try:
                self.sender.send_nowait({"type": typ, "value": value})
            except trio.WouldBlock:
                pass
            except e:
                self.sender.close
                raise e
            else:
                break

    def send(self, text):
        if not text:
            return

        lang = detect(text)

        self.send_event("request", {"text": text, "lang": lang})

        self.messages.append({"text": text, "sent": True, "pos_hint": {"right": 1}})

        # scroll to bottom
        self.scroll_to_bottom()

    def receive(self, value):
        text = value["text"]
        self.messages.append({"text": text, "sent": False})
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        rv = self.ids.chat_rv
        box = self.ids.chat_box
        if rv.height < box.height:
            Animation.cancel_all(rv, "scroll_y")
            Animation(scroll_y=0, t="out_quad", d=0.5).start(rv)

    def record_message(self):
        self.send_event("record", None)

    def toggle_mute(self, button: MDIconButton):
        self.mute = not self.mute
        if self.mute:
            button.icon = "volume-mute"
            button.text_color = MDApp.get_running_app().theme_cls.accent_color
        else:
            button.icon = "volume-high"
            button.text_color = MDApp.get_running_app().theme_cls.icon_color
        print(f"volumen: {1 - int(self.mute)}")
        self.send_event("set-volume", 1 - int(self.mute))

    def show_recording_popup(self, show: bool):
        card = self.ids.recording_popup
        if show:
            card.disabled = False
            card.opacity = 0.0
            anim = Animation(opacity=1, t="in_out_sine", duration=2.0) + Animation(
                opacity=0.3, t="in_out_sine", duration=2.0
            )
            anim.repeat = True
            anim.start(card)
        else:
            Animation.cancel_all(card, "opacity")
            card.disabled = True
            card.opacity = 0.0

class ChatApp(MDApp):
    def build(self):
        print("Building root widget")
        self.chat = Chat(self.event_sender)
        return self.chat

    async def app_func(self):
        print("Starting app")
        self.title = "La Rodadora"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Cyan"
        print(self.theme_cls)

        async with trio.open_nursery() as nursery:
            chatbot_sender, chatbot_receiver = trio.open_memory_channel(5)
            tts_sender, tts_receiver = trio.open_memory_channel(5)
            event_sender, event_receiver = trio.open_memory_channel(5)
            self.event_sender = event_sender.clone()

            async def run_wrapper():
                await self.async_run(async_lib="trio")
                print("Exiting...")
                with self.event_sender:
                    await self.event_sender.send({"type": "exit"})
                await self.event_sender.aclose()

            nursery.start_soon(run_wrapper)
            nursery.start_soon(
                self.handle_events,
                chatbot_sender,
                tts_sender,
                self.event_sender,
                event_receiver,
            )
            nursery.start_soon(
                trio.to_thread.run_sync,
                chatbot,
                chatbot_receiver,
                event_sender.clone(),
            )
            nursery.start_soon(
                trio.to_thread.run_sync, tts, tts_receiver, event_sender.clone()
            )

    async def handle_events(
        self, chatbot_sender, tts_sender, events_sender, events_receiver
    ):
        async with trio.open_nursery() as nursery, chatbot_sender, tts_sender, events_receiver:
            async for event in events_receiver:
                match event["type"]:
                    case "request":
                        nursery.start_soon(
                            chatbot_sender.send, {"value": event["value"], "tts": False}
                        )
                    case "request-tts":
                        nursery.start_soon(
                            chatbot_sender.send, {"value": event["value"], "tts": True}
                        )
                    case "response":
                        self.chat.receive(event["value"])
                    case "response-tts":
                        self.chat.receive(event["value"])
                        nursery.start_soon(
                            tts_sender.send, {"type": "say", "value": event["value"]}
                        )
                    case "set-volume":
                        nursery.start_soon(tts_sender.send, event)
                    case "record":
                        nursery.start_soon(
                            trio.to_thread.run_sync,
                            record,
                            events_sender.clone(),
                        )
                    case "started-recording":
                        self.chat.show_recording_popup(True)
                    case "stopped-recording":
                        self.chat.show_recording_popup(False)
                    case "exit":
                        nursery.cancel_scope.cancel()

if __name__ == "__main__":
    Window.size = (1000, 700)

    trio.run(ChatApp().app_func)
