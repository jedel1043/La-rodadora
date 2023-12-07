import logging
import trio
from chatbot import PolyglotChatbot, PredictionError, UnsupportedLang
from gui.tasks.utils import emit

feedback_responses = {
    "es": [
        "Lo siento, no cuento con dicha informacion o no pude entender bien su pregunta. Por favor vuelve a enviar tu pregunta para realizar la retroalimentación",
        "Por favor vuelve a enviar la respuesta para realizar la retroalimentación",
        "Por favor digita la clave para realizarla.",
        "Clave correcta, realizando retroalimentación.",
        "Retroalimentación lista, reiniciando a Ruby...",
        "Clave incorrecta, deshaciendo los cambios.",
    ],
    "en": [
        "I'm sorry, I don't have that information or I couldn't understand your question. Please ask your question again to begin feedback.",
        "Please send the answer to the question to begin feedback.",
        "Please type the password to begin.",
        "Password accepted, starting feedback.",
        "Finished feedback, restarting Ruby...",
        "Incorrect password, undoing changes.",
    ],
}


def chatbot(receiver: trio.MemoryReceiveChannel, sender: trio.MemorySendChannel):
    chat_bot = PolyglotChatbot(["en", "es"])

    while True:
        try:
            request = trio.from_thread.run(receiver.receive)
            if not request:
                continue

            question = request["text"]
            lang = request["lang"]
            is_tts = request["tts"]

            logging.debug(
                f"Chat requested: question: '{question}', lang: '{lang}', tts: {is_tts}"
            )

            try:
                answer = chat_bot.chat(question, lang)
                logging.debug(f"Chatbot response: answer: {answer}")
                msg = {"text": answer, "lang": lang, "tts": is_tts}
                emit(sender, "response", msg)
            except PredictionError:
                logging.info("fallo encontrado con texto '{question}'")
                logging.info("retroalimentando")
                emit(
                    sender,
                    "response",
                    {"text": feedback_responses[lang][0], "lang": lang, "tts": False},
                )
                new_question = trio.from_thread.run(receiver.receive)["text"]
                emit(
                    sender,
                    "response",
                    {"text": feedback_responses[lang][1], "lang": lang, "tts": False},
                )
                new_answer = trio.from_thread.run(receiver.receive)["text"]
                emit(
                    sender,
                    "response",
                    {"text": feedback_responses[lang][2], "lang": lang, "tts": False},
                )
                password = trio.from_thread.run(receiver.receive)["text"]

                if password.lower() == "ciita":
                    emit(
                        sender,
                        "response",
                        {
                            "text": feedback_responses[lang][3],
                            "lang": lang,
                            "tts": False,
                        },
                    )
                    chat_bot.retroalimentacion(question, [new_answer], lang)
                    emit(
                        sender,
                        "response",
                        {
                            "text": feedback_responses[lang][4],
                            "lang": lang,
                            "tts": False,
                        },
                    )
                    chat_bot = PolyglotChatbot()
                else:
                    emit(
                        sender,
                        "response",
                        {
                            "text": feedback_responses[lang][5],
                            "lang": lang,
                            "tts": False,
                        },
                    )
        except UnsupportedLang:
            logging.warning(f"Tried to chat in unsupported language '{lang}'")
            emit(sender, "response", {"text": "Unsupported language", "lang": "en"})
        except trio.EndOfChannel:
            logging.info("Closing chatbot thread")
            trio.from_thread.run(sender.aclose)
            return
        except trio.BrokenResourceError as e:
            logging.error(e)
            raise e
        except Exception as e:
            logging.error(e)
            trio.from_thread.run(sender.aclose)
            raise e
