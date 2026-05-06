import os

from keysuite.config import RuntimeConfig


def test_runtime_config_priority_and_toml_macros(tmp_path, monkeypatch):
    toml_path = tmp_path / "keysuite.toml"
    toml_path.write_text(
        """
grammar = "grammar/from-toml.yaml"
max_buffer_size = 12
version_policy = "strict"

[macros]
pair = ["C", "C"]
""".strip()
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("KEYSUITE_GRAMMAR", "grammar/from-env.yaml")
    monkeypatch.setenv("KEYSUITE_MAX_BUFFER_SIZE", "9")
    monkeypatch.setenv("KEYSUITE_DEBUG", "1")

    cfg = RuntimeConfig.from_sources(
        explicit={"grammar_path": "grammar/explicit.yaml", "max_buffer_size": 7},
        env={},
        toml_path=toml_path,
    )

    assert cfg.grammar_path == "grammar/explicit.yaml"
    assert cfg.max_buffer_size == 7
    assert cfg.debug_level == 0
    assert cfg.version_policy == "strict"
    assert cfg.macros["pair"] == ["C", "C"]

    env_cfg = RuntimeConfig.from_sources(env=os.environ, toml_path=toml_path)
    assert env_cfg.grammar_path == "grammar/from-env.yaml"
    assert env_cfg.max_buffer_size == 9
    assert env_cfg.debug_level == 1
