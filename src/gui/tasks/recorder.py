import trio
import speech_recognition as sr
from langdetect import detect
from gui.tasks.utils import emit

def record(sender: trio.MemorySendChannel):
    try:
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            emit(sender, "started-recording")
            audio = recognizer.listen(source, timeout=10)
            emit(sender, "stopped-recording")

            text = recognizer.recognize_whisper(audio, language="es", model="small")
            lang = detect(text)

            emit(sender, "request-tts", {"text": text, "lang": lang})
    except sr.RequestError as e:
        emit(
            sender,
            "response",
            f"Error al grabar audio: {e}",
        )
    except sr.UnknownValueError:
        emit(sender, "response", "Google Speech Recognition no pudo entender el audio")
    except sr.WaitTimeoutError:
        emit(sender, "response", "Se alcanzó el tiempo límite para grabar una pregunta.")
    except trio.BrokenResourceError as e:
        print("Tried to send event to broken resource.")
    except Exception as e:
        print(sender, "response", f"Error en la grabación: {e}")
    trio.from_thread.run(sender.aclose)
