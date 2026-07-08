import os
import pathlib
import yaml


def get_data_dir() -> pathlib.Path:
    repo_path = os.environ.get("ARCH_REPO_PATH")
    if repo_path:
        return pathlib.Path(repo_path) / "data"
    return pathlib.Path(__file__).parent.parent / "data"


def load_all(data_dir: pathlib.Path | None = None) -> tuple[dict, dict]:
    """Returns (entity_yamls, enum_yamls).

    entity_yamls: {stem: {"objects": [...]}}  — YAML files whose root is a dict
    enum_yamls:   {stem: {"items": [...]}}     — YAML files whose root is a list
    """
    if data_dir is None:
        data_dir = get_data_dir()

    entity_yamls: dict = {}
    enum_yamls: dict = {}

    for file in sorted(pathlib.Path(data_dir).glob("*.yaml")):
        data = yaml.safe_load(file.read_text(encoding="utf-8"))
        stem = file.stem
        if isinstance(data, dict):
            entity_yamls[stem] = data
        elif isinstance(data, list):
            enum_yamls[stem] = {"items": data}

    return entity_yamls, enum_yamls
