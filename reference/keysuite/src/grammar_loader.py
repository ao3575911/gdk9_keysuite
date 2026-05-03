import yaml


def _unwrap_grammar(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("GDk9 grammar must be a mapping")
    return data.get("gdk9_grammar", data)


def load_grammar(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return _unwrap_grammar(yaml.safe_load(f))
