from kivy.graphics.svg import Svg
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import StringProperty, ListProperty
from kivy.core.window import Window
from kivy.animation import Animation

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.widget import MDWidget
import sounddevice as sd
import speech_recognition as sr
import components
from queue import Queue
from threading import Thread
from chatbot import Chatbot
import pyttsx3


chat_bot = Chatbot()

class Chat(MDWidget):
    messages = ListProperty([])

    def __init__(self):
        super().__init__()
        self.requests = Queue()

        def chatter():

            while True:
                item = self.requests.get()
                if item is None:
                    break

                response = chat_bot.chat(item)
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
        def record_and_transcribe():
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=1) 
            self.receive("Puedes hablar...")
            with microphone as source:
                audio = recognizer.listen(source, timeout=15)
            try:
                text = recognizer.recognize_google(audio, language="es")
                response = chat_bot.chat(text)
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                engine.say(response)
                engine.runAndWait()
                self.receive("Espero que mi respuesta te sea de mucha ayuda")
            except sr.RequestError as e:
                self.receive(f"Error en la solicitud a la API de Google Speech Recognition: {e}")
            except sr.UnknownValueError:
                self.receive("Google Speech Recognition no pudo entender el audio")
            except Exception as e:
                self.receive(f"Error durante la grabación o transcripción: {str(e)}")
        recording_thread = Thread(target=record_and_transcribe)
        recording_thread.start()


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
