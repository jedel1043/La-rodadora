import trio
from chatbot import PolyglotChatbot, PredictionError, UnsupportedLang
from gui.tasks.utils import emit

def chatbot(receiver: trio.MemoryReceiveChannel, sender: trio.MemorySendChannel):
    chat_bot = PolyglotChatbot()

    while True:
        try:
            request = trio.from_thread.run(receiver.receive)
            if not request:
                continue

            value = request["value"]
            question = value["text"]
            lang = value["lang"]
            is_tts = request["tts"]

            print(question)
            print(lang)

            try:
                answer = chat_bot.chat(question, lang)
                print(answer)
                msg = {"text": answer, "lang": lang}
                if is_tts:
                    emit(sender, "response-tts", msg)
                else:
                    emit(sender, "response", msg)
            except PredictionError:
                print("fallo encontrado, texto: ", question)
                print("retroalimentando")
                emit(
                    sender,
                    "response",
                    "Lo siento, no cuento con dicha informacion o no pude entender bien su pregunta. Por favor vuelve a enviar tu pregunta para realizar la retroalimentación",
                )
                new_question = trio.from_thread.run(receiver.receive)["value"]
                emit(
                    sender,
                    "response",
                    "Por favor vuelve a enviar la respuesta para realizar la retroalimentación",
                )
                new_answer = trio.from_thread.run(receiver.receive)["value"]
                emit(sender, "response", "Por favor digita la clave para realizarla.")
                password = trio.from_thread.run(receiver.receive)["value"]

                if password.lower() == "ciita":
                    emit(
                        sender,
                        "response",
                        "Clave correcta, realizando retroalimentación.",
                    )
                    chat_bot.retroalimentacion(question, [new_answer], lang)
                    emit(
                        sender,
                        "response",
                        "Retroalimentación lista, reiniciando a Ruby...",
                    )
                    chat_bot = PolyglotChatbot()
                else:
                    emit(
                        sender, "response", "Clave incorrecta, deshaciendo los cambios."
                    )
        except UnsupportedLang:
            emit(
                sender, "response", { "text": "Unsupported language", "lang": "en" }
            )
        except trio.EndOfChannel:
            print("Closing tts thread")
            trio.from_thread.run(sender.aclose)
            return
        except trio.BrokenResourceError as e:
            print("Tried to send event to broken resource.")
            trio.from_thread.run(sender.aclose)
            raise e
        except Exception as e:
            print("Closing tts thread with error")
            trio.from_thread.run(sender.aclose)
            raise e
