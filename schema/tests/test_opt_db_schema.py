from pathlib import Path
import json
import referencing
import jsonschema.validators
import urllib
import yaml

script_dir = Path(__file__).parent
schema_dir = script_dir / ".." / "generated" / "opt_db_schema"
tests_dir = script_dir / "opt_db_schema"


def file_retrieve(uri):
    print(urllib.parse.urlparse(uri).path)
    path = schema_dir / urllib.parse.urlparse(uri).path.removeprefix("/")
    result = json.loads(path.read_text(encoding="utf-8"))
    return referencing.Resource.from_contents(result)


registry = referencing.Registry(retrieve=file_retrieve)


for f in tests_dir.glob("*.yaml"):
    schema_name = f.with_suffix(".schema.json").name

    print(f"Testing {f.name} against {schema_name}")

    schema = registry.get_or_retrieve(schema_name).value.contents
    validator = jsonschema.validators.validator_for(schema)(schema, registry=registry)
    validator.validate(yaml.safe_load(f.read_bytes()))
