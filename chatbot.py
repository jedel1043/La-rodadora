import random
import json
import pickle
import unicodedata
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from transcriber import transcribe_speech, reproducir_audio
from keras.models import load_model
from train import train

def lector():
    with open('data.json', encoding='utf-8') as file:
        intents = json.load(file)
    return intents

def get_response(intents_list, intents_json):
    tag = intents_list[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
    return result

class Chatbot:
    def __init__(self):
        nltk.download('punkt', quiet=True)
        nltk.download('wordnet', quiet=True)
        self.lemmatizer = WordNetLemmatizer()
        self.retroalimentacion_status = False
        self.model = load_model('chat.h5')
        print("Encendido.")

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
        classes = pickle.load(open('classes.pkl', 'rb'))
        words = pickle.load(open('words.pkl', 'rb'))
        msg = ''.join((c for c in unicodedata.normalize('NFD', sentence) if unicodedata.category(c) != 'Mn'))
        bow = self.bag_of_word(msg.lower(), words)
        res = self.model.predict(np.array([bow]))[0]
        ERROR_THRESHOLD = 0.4
        results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
        results.sort(key=lambda x: x[1], reverse=True)
        return_list = []
        for r in results:
            return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})
        return return_list

    def retroalimentacion(self, text: str):
        intents = lector()
        datas = intents['intents']
        responses = []
        response = input("Por favor coloca la respuesta que deseas ante tu pregunta: ")
        responses.append(response)
        dicts = {'tag': text, 'patterns': [text], 'responses': responses}
        datas.append(dicts)
        dicts = {"intents": datas, "error": intents['error']}
        with open('data.json','w' ,encoding='utf-8') as file:
            json.dump(dicts,file, indent=4)
            file.close()
        self.retroalimentacion_status = True
        train()

    def chat(self, message: str):
        try:
            intents = lector()
            ints = self.predict_class(message)
            if ints:
                return get_response(ints, intents)
            else:
                return intents['error']
        except Exception as e:
            print(f"Error en funcion chatbot: {e}")