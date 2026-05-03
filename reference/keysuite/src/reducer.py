def reduce_buffer(buffer: list[str], mode: str | None = None) -> str:
    if "." in buffer:
        i = buffer.index(".")
        result = "".join(buffer[:i]) + "→" + "".join(buffer[i + 1:])
    else:
        result = "".join(buffer)
    return f"{mode}({result})" if mode else result
