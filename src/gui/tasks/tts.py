from enum import Enum
from collections.abc import Iterable, MutableMapping
from dataclasses import dataclass
import trio
import pyttsx3
from pyttsx3.voice import Voice
import numpy as np
from gui.tasks.utils import emit
import logging


class BaseLanguage(Enum):
    SPANISH = 0
    ENGLISH = 1


@dataclass
class MissingLanguageSupport(Exception):
    """Raised when the tts doesn't support a required language"""

    language: BaseLanguage

@dataclass
class UnsupportedLanguage(Exception):
    """Raised when the tts doesn't support a requested language"""

    language: str

@dataclass
class Language:
    base_language: BaseLanguage
    language_id: str
    priority: int


supported_langs = [
    # Mexican spanish
    Language(BaseLanguage.SPANISH, "es-mx", 15),
    # Latin american spanish
    Language(BaseLanguage.SPANISH, "es-419", 10),
    # American english
    Language(BaseLanguage.ENGLISH, "en-us", 10),
    # American english (New York)
    Language(BaseLanguage.ENGLISH, "en-us-nyc", 9),
    # European spanish
    Language(BaseLanguage.SPANISH, "es", 5),
    # British english
    Language(BaseLanguage.ENGLISH, "en-gb", 5),
    # Neutral english
    Language(BaseLanguage.ENGLISH, "en", 5),
]


def find_voices(available: Iterable[Voice]) -> dict[BaseLanguage, str]:
    result: dict[BaseLanguage, (str, int)] = {}

    for voice in available:
        for lang in supported_langs:
            if (
                lang.language_id in voice.languages
                and lang.priority > result.get(lang.base_language, ("", -1))[1]
            ):
                result[lang.base_language] = (voice.id, lang.priority)

    return dict((base, lang_id) for (base, (lang_id, _)) in result.items())


def tts(receiver: trio.MemoryReceiveChannel, sender: trio.MemorySendChannel):
    tts = pyttsx3.init()
    tts.setProperty("rate", 150)

    voices = find_voices(tts.getProperty("voices"))

    if (es := voices.get(BaseLanguage.SPANISH)) is None:
        raise MissingLanguageSupport(BaseLanguage.SPANISH)
    if (en := voices.get(BaseLanguage.ENGLISH)) is None:
        raise MissingLanguageSupport(BaseLanguage.ENGLISH)

    logging.info(f"Selected voice for ES: {es}")
    logging.info(f"Selected voice for EN: {en}")

    while True:
        try:
            request = trio.from_thread.run(receiver.receive)
            match request["type"]:
                case "set-volume":
                    tts.setProperty("volume", min(max(request["value"], 1.0), 0.0))
                case "say":
                    value = request["value"]
                    lang = value["lang"]
                    text = value["text"]
                    logging.debug("Requested TTS: text: {text}, lang: {lang}")
                    print(value)
                    if lang == "es":
                        tts.setProperty('voice', es)
                    elif lang == "en":
                        tts.setProperty('voice', en)
                    else:
                        raise UnsupportedLanguage(lang)
                    tts.say(text)
                    tts.runAndWait()
        except trio.EndOfChannel:
            logging.info("Closing tts thread")
            trio.from_thread.run(sender.aclose)
            return
        except trio.BrokenResourceError as e:
            logging.error(e)
            raise e
        except Exception as e:
            logging.error(e)
            trio.from_thread.run(sender.aclose)
            raise e
