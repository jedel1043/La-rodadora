import random
import json
import pickle
import unicodedata
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from keras.models import load_model

from pathlib import Path

from .train import train

parent_dir = Path(__file__).parent

class PredictionError(Exception):
    """Raised when the predictor could not find a suitable answer"""

    pass


class UnsupportedLang(Exception):
    """Raised when the predictor doesn't support a provided language"""

    pass

def get_response(intents_list, intents_json):
    tag = intents_list[0]["intent"]
    list_of_intents = intents_json["intents"]
    for i in list_of_intents:
        if i["tag"] == tag:
            result = random.choice(i["responses"])
            break
    return result

class Chatbot:
    def __init__(self, language: str):
        try:
            self.datapath = parent_dir / "data" / language
            nltk.download("punkt", quiet=True)
            nltk.download("wordnet", quiet=True)
            self.lemmatizer = WordNetLemmatizer()
            self.retroalimentacion_status = False
            self.model = load_model(self.datapath / "chat.h5")
            print(f"Chatbot for language `{language}` enabled.")
        except:
            raise UnsupportedLang

    def clean_up_sentence(self, sentence):
        sentence_words = nltk.word_tokenize(sentence)
        sentence_words = [self.lemmatizer.lemmatize(word) for word in sentence_words]
        return sentence_words

    def bag_of_word(self, sentence, words):
        sentence_words = self.clean_up_sentence(sentence)
        bag = [0] * len(words)
        for w in sentence_words:
            for i, word in enumerate(words):
                if word == w:
                    bag[i] = 1
        return np.array(bag)

    def predict_class(self, sentence):
        print(self.model)
        classes = pickle.load(open(self.datapath / "classes.pkl", "rb"))
        words = pickle.load(open(self.datapath / "words.pkl", "rb"))
        msg = "".join(
            (
                c
                for c in unicodedata.normalize("NFD", sentence)
                if unicodedata.category(c) != "Mn"
            )
        )
        bow = self.bag_of_word(msg.lower(), words)
        res = self.model.predict(np.array([bow]))[0]
        ERROR_THRESHOLD = 0.4
        results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
        results.sort(key=lambda x: x[1], reverse=True)
        return_list = []
        for r in results:
            return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
        return return_list

    def retroalimentacion(self, text: str, responses: list):
        intents = lector()
        datas = intents["intents"]
        dicts = {"tag": text, "patterns": [text], "responses": responses}
        datas.append(dicts)
        dicts = {"intents": datas, "error": intents["error"]}
        with open(parent_dir / "data.json", "w", encoding="utf-8") as file:
            json.dump(dicts, file, indent=4)
            file.close()
        self.retroalimentacion_status = True
        train(self.datapath)

    def lector(self):
        with open(self.datapath / "raw.json", encoding="utf-8") as file:
            return json.load(file)

    def chat(self, message: str):
        try:
            intents = self.lector()
            ints = self.predict_class(message)
            if ints:
                return get_response(ints, intents)
        except Exception as e:
            raise PredictionError


class PolyglotChatbot:
    def __init__(self, langs: [str]):
        self.models: dict[str, Chatbot] = {}
        for lang in langs:
            models[lang] = Chatbot(lang)

    def chat(self, message: str, lang: str):
        if lang not in self.models:
            raise UnsupportedLang

        self.models[lang].chat(message)

    def retroalimentacion(self, text: str, responses: list, lang: str):
        if lang not in self.models:
            raise UnsupportedLang

        self.models[lang].retroalimentacion(text, responses)
