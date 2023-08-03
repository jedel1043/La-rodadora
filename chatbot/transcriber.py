import speech_recognition as sr
import pyttsx3

def transcribe_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio, language="es")
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            return None

def reproducir_audio(texto):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(texto)
    engine.runAndWait()