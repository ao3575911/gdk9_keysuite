from .symbols import symbol_text


class IMEKernel:
    def __init__(self, transitions: dict, reducer):
        self.transitions = transitions
        self.reducer = reducer
        self.reset()

    def reset(self):
        self.state = "IDLE"
        self.buffer = []
        self.mode = None

    def handle(self, event: dict):
        event_class = event["class"]
        value = event.get("value")
        rule = self.transitions.get(self.state, {}).get(event_class)

        if rule is None:
            self.state = "ERROR"
            return None

        next_state, action = rule
        output = self.apply(action, value)
        self.state = next_state
        return output

    def apply(self, action: str, value):
        if action == "append":
            self.buffer.append(value)
        elif action == "mark_bind":
            self.buffer.append(".")
        elif action == "set_mode":
            self.mode = "".join(symbol_text(symbol) for symbol in self.buffer) if self.buffer else None
            self.buffer.clear()
        elif action == "pop":
            if self.buffer:
                self.buffer.pop()
        elif action == "clear":
            self.reset()
        elif action == "reduce_and_emit":
            output = self.reducer(self.buffer, self.mode)
            self.reset()
            return output
        return None
