import json
import urllib
from pathlib import Path

import jsonschema.validators
import referencing


def make_registry(schema_dir: Path) -> referencing.Registry:
    def file_retrieve(uri):
        path = schema_dir / urllib.parse.urlparse(uri).path.removeprefix("/")
        result = json.loads(path.read_text(encoding="utf-8"))
        return referencing.Resource.from_contents(result)

    return referencing.Registry(retrieve=file_retrieve)


def get_validator(registry: referencing.Registry, schema_name: str):
    schema = registry.get_or_retrieve(schema_name).value.contents
    return jsonschema.validators.validator_for(schema)(schema, registry=registry)
