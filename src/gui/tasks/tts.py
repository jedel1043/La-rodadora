import trio
import pyttsx3
import numpy as np
from gui.tasks.utils import emit


def tts(receiver: trio.MemoryReceiveChannel, sender: trio.MemorySendChannel):
    tts = pyttsx3.init()
    tts.setProperty("rate", 150)
    print(tts.getProperty('voice'))
    print(tts.getProperty('voices'))
    while True:
        try:
            request = trio.from_thread.run(receiver.receive)
            match request["type"]:
                case "set-volume":
                    tts.setProperty("volume", min(max(request["value"], 1.0), 0.0))
                case "say":
                    tts.say(request["value"])
                    tts.runAndWait()
        except trio.EndOfChannel:
            print("Closing tts thread")
            trio.from_thread.run(sender.aclose)
            return
        except trio.BrokenResourceError as e:
            print("Tried to send event to broken resource.")
            raise e
        except Exception as e:
            print("Closing tts thread with error")
            trio.from_thread.run(sender.aclose)
            raise e
