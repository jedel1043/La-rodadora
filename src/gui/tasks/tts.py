from enum import Enum
from collections.abc import Iterable, MutableMapping
from dataclasses import dataclass
from langcodes import Language
from langcodes.tag_parser import LanguageTagError
from typing import List, Tuple
import trio
import pyttsx3
from pyttsx3.voice import Voice
import numpy as np
from gui.tasks.utils import emit
import logging


@dataclass
class TTSVoice:
    language: Language
    id: str


@dataclass
class MissingLanguageSupport(Exception):
    """Raised when the tts is missing support from the system for a required language"""

    language: Language


@dataclass
class UnknownLanguage(Exception):
    """Raised when the tts doesn't support a requested language"""

    language: str


ES_MX = Language.get("es-MX")
EN_US = Language.get("en-US")


def find_voices(
    available: Iterable[Voice], requested: List[Language]
) -> dict[Language, TTSVoice]:
    tts_voices = []
    for v in available:
        for lang in v.languages:
            try:
                candidate = TTSVoice(Language.get(lang), v.id)
                tts_voices.append(candidate)
            except LanguageTagError:
                pass

    result: dict[Language, Tuple[TTSVoice, int]] = {}

    for voice in tts_voices:
        for req in requested:
            distance = req.distance(req)
            if distance <= 25 and distance < result.get(req, (None, 255))[1]:
                result[req] = (voice, distance)

    return dict((lang, voice) for (lang, (voice, _)) in result.items())


def tts(receiver: trio.MemoryReceiveChannel, sender: trio.MemorySendChannel):
    tts = pyttsx3.init()
    tts.setProperty("rate", 150)

    voices = find_voices(
        tts.getProperty("voices"), [Language.get("es-MX"), Language.get("en-US")]
    )

    if (es := voices.get(ES_MX)) is None:
        raise MissingLanguageSupport(ES_MX)
    if (en := voices.get(EN_US)) is None:
        raise MissingLanguageSupport(EN_US)

    logging.info(f"Selected voice for ES: {es}")
    logging.info(f"Selected voice for EN: {en}")

    while True:
        try:
            request = trio.from_thread.run(receiver.receive)
            match request["type"]:
                case "set-volume":
                    pass
                    tts.setProperty("volume", min(max(request["value"], 1.0), 0.0))
                case "say":
                    pass
                    value = request["value"]
                    lang = value["lang"]
                    text = value["text"]
                    logging.debug("Requested TTS: text: {text}, lang: {lang}")
                    print(value)
                    if lang == "es":
                        tts.setProperty("voice", es.id)
                    elif lang == "en":
                        tts.setProperty("voice", en.id)
                    else:
                        raise UnknownLanguage(lang)
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
