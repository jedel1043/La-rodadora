import pythoncom
import time
import math
import os
import sys
import weakref
import ctypes
from ctypes import WINFUNCTYPE, windll, c_int, WinError, c_wchar_p, wstring_at, create_unicode_buffer
from ctypes.wintypes import LCID, LPWSTR, DWORD
from ..voice import Voice
from . import toUtf8, fromUtf8

def winfunc(name, dll, result, *args):
    '''build and apply a ctypes prototype complete with parameter flags'''
    atypes = []
    aflags = []
    for arg in args:
        atypes.append(arg[1])
        aflags.append((arg[2], arg[0]) + arg[3:])
    prototype = ctypes.WINFUNCTYPE(result, *atypes, use_last_error=True)
    return prototype((name, dll), tuple(aflags))

LCIDToLocaleName = winfunc(
    'LCIDToLocaleName', windll.kernel32, c_int,
    ("Locale", LCID, 1),
    ("lpName", LPWSTR, 1),
    ("cchName", c_int, 1),
    ("dwFlags", DWORD, 1),
)

def LCIDToLocaleName_errcheck(result: c_int, func, args) -> str:
    if result == 0:
        raise WinError(ctypes.get_last_error())
    return args

LCIDToLocaleName.errcheck = LCIDToLocaleName_errcheck

from comtypes.client import GetEvents, CreateObject

if not hasattr(sys, "frozen"):
    from comtypes.client import GetModule
    GetModule("Speech\\Common\\sapi.dll")

from comtypes.gen import SpeechLib

# common voices
MSSAM = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\MSSam'
MSMARY = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\MSMary'
MSMIKE = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\MSMike'

# coeffs for wpm conversion
E_REG = {MSSAM: (137.89, 1.11),
         MSMARY: (156.63, 1.11),
         MSMIKE: (154.37, 1.11)}


def buildDriver(proxy):
    return SAPI5Driver(proxy)


class SAPI5Driver(object):
    def __init__(self, proxy):
        self._tts = CreateObject('SAPI.SPVoice')
        # all events
        self._tts.EventInterests = 33790
        self._event_sink = SAPI5DriverEventSink()
        self._event_sink.setDriver(weakref.proxy(self))
        self._advise = GetEvents(self._tts, self._event_sink)
        self._proxy = proxy
        self._looping = False
        self._speaking = False
        self._stopping = False
        # initial rate
        self._rateWpm = 200
        self.setProperty('voice', self.getProperty('voice'))

    def destroy(self):
        self._tts.EventInterests = 0

    def say(self, text):
        self._proxy.setBusy(True)
        self._proxy.notify('started-utterance')
        self._speaking = True
        self._tts.Speak(fromUtf8(toUtf8(text)))

    def stop(self):
        if not self._speaking:
            return
        self._proxy.setBusy(True)
        self._stopping = True
        self._tts.Speak('', 3)

    def save_to_file(self, text, filename):
        cwd = os.getcwd()
        stream = CreateObject('SAPI.SPFileStream')
        stream.Open(filename, SpeechLib.SSFMCreateForWrite)
        temp_stream = self._tts.AudioOutputStream
        self._tts.AudioOutputStream = stream
        self._tts.Speak(fromUtf8(toUtf8(text)))
        self._tts.AudioOutputStream = temp_stream
        stream.close()
        os.chdir(cwd)

    def _toVoice(self, attr):
        language = int(attr.getAttribute("Language"), base=16)
        buffer = create_unicode_buffer(85)
        result = LCIDToLocaleName(language, buffer, 85, 0)
        locale = ctypes.wstring_at(buffer, int(result) - 1)

        gender: str = attr.getAttribute("Gender")
        age: str = attr.getAttribute("Age")

        return Voice(attr.Id, attr.GetDescription(), languages=[locale], gender=gender, age=age)

    def _tokenFromId(self, id_):
        tokens = self._tts.GetVoices()
        for token in tokens:
            if token.Id == id_:
                return token
        raise ValueError('unknown voice id %s', id_)

    def getProperty(self, name):
        if name == 'voices':
            return [self._toVoice(attr) for attr in self._tts.GetVoices()]
        elif name == 'voice':
            return self._tts.Voice.Id
        elif name == 'rate':
            return self._rateWpm
        elif name == 'volume':
            return self._tts.Volume / 100.0
        else:
            raise KeyError('unknown property %s' % name)

    def setProperty(self, name, value):
        if name == 'voice':
            token = self._tokenFromId(value)
            self._tts.Voice = token
            a, b = E_REG.get(value, E_REG[MSMARY])
            self._tts.Rate = int(math.log(self._rateWpm / a, b))
        elif name == 'rate':
            id_ = self._tts.Voice.Id
            a, b = E_REG.get(id_, E_REG[MSMARY])
            try:
                self._tts.Rate = int(math.log(value / a, b))
            except TypeError as e:
                raise ValueError(str(e))
            self._rateWpm = value
        elif name == 'volume':
            try:
                self._tts.Volume = int(round(value * 100, 2))
            except TypeError as e:
                raise ValueError(str(e))
        else:
            raise KeyError('unknown property %s' % name)

    def startLoop(self):
        first = True
        self._looping = True
        while self._looping:
            if first:
                self._proxy.setBusy(False)
                first = False
            pythoncom.PumpWaitingMessages()
            time.sleep(0.05)

    def endLoop(self):
        self._looping = False

    def iterate(self):
        self._proxy.setBusy(False)
        while 1:
            pythoncom.PumpWaitingMessages()
            yield


class SAPI5DriverEventSink(object):
    def __init__(self):
        self._driver = None

    def setDriver(self, driver):
        self._driver = driver

    def _ISpeechVoiceEvents_StartStream(self, char, length):
        self._driver._proxy.notify(
            'started-word', location=char, length=length)

    def _ISpeechVoiceEvents_EndStream(self, stream, pos):
        d = self._driver
        if d._speaking:
            d._proxy.notify('finished-utterance', completed=not d._stopping)
        d._speaking = False
        d._stopping = False
        d._proxy.setBusy(False)
