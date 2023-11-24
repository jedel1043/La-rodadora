import trio

def emit(sender: trio.MemorySendChannel, typ: str, value=None):
    trio.from_thread.run(sender.send, {"type": typ, "value": value})