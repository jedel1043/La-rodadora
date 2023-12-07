import trio
import speech_recognition as sr
import logging
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

            result = recognizer.recognize_whisper(audio, model="medium", show_dict=True)
            text = result["text"]
            lang = result["language"]

            logging.debug(f"New recording: text: {text}, lang: {lang}")

            emit(sender, "request", {"text": text, "lang": lang, "tts": True})
    except sr.RequestError as e:
        emit(
            sender,
            "response",
            f"Error al grabar audio: {e}",
        )
    except sr.UnknownValueError:
        emit(sender, "response", "Se tuvo problemas para entender el audio.")
    except sr.WaitTimeoutError:
        emit(
            sender, "response", "Se alcanzó el tiempo límite para grabar una pregunta."
        )
    except Exception as e:
        logging.warning(e)
        logging.warning("ignoring record request")
    trio.from_thread.run(sender.aclose)
