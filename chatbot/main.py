import random
import json
import pickle
import unicodedata
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from chatbot.transcriber import transcribe_speech, reproducir_audio
from keras.models import load_model
from chatbot.train import train


nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
lemmatizer = WordNetLemmatizer()

retroalimentacion_status = False

model = load_model('chatbot/chat.h5')

def lector():
    with open('chatbot/data.json', encoding='utf-8') as file:
        intents = json.load(file)
    return intents

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word) for word in sentence_words]
    return sentence_words

def bag_of_word(sentence, words):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence, model):
    classes = pickle.load(open('chatbot/classes.pkl', 'rb'))
    words = pickle.load(open('chatbot/words.pkl', 'rb'))
    msg = ''.join((c for c in unicodedata.normalize('NFD', sentence) if unicodedata.category(c) != 'Mn'))
    bow = bag_of_word(msg.lower(), words)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.4
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})
    return return_list

def get_response(intents_list, intents_json):
    tag = intents_list[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
    return result

print("Encendido.")

def retroalimentacion(text: str):
    intents = lector()
    datas = intents['intents']
    responses = []
    response = input("Por favor coloca la respuesta que deseas ante tu pregunta: ")
    responses.append(response)
    dicts = {'tag': text, 'patterns': [text], 'responses': responses}
    datas.append(dicts)
    dicts = {"intents": datas, "error": intents['error']}
    with open('chatbot/data.json','w' ,encoding='utf-8') as file:
        json.dump(dicts,file, indent=4)
        file.close()
    global retroalimentacion_status
    retroalimentacion_status = True
    train()

def chatbot(message: str):
    try:
        intents = lector()
        ints = predict_class(message, model)
        if ints:
            return get_response(ints, intents)
        else:
            return intents['error']
    except Exception as e:
        print(f"Error en funcion chatbot: {e}")