from pathlib import Path
import json
import referencing
import jsonschema.validators
import urllib
import yaml

script_dir = Path(__file__).parent
schema_dir = script_dir / ".." / "generated" / "opt_db_schema"
data_dir = script_dir / ".." / ".." / "data"


def file_retrieve(uri):
    path = schema_dir / urllib.parse.urlparse(uri).path.removeprefix("/")
    result = json.loads(path.read_text(encoding="utf-8"))
    return referencing.Resource.from_contents(result)


registry = referencing.Registry(retrieve=file_retrieve)

schema = registry.get_or_retrieve("fff_material_properties.schema.json").value.contents
validator = jsonschema.validators.validator_for(schema)(schema, registry=registry)

material_types = yaml.safe_load((data_dir / "fff_material_types.yaml").read_bytes())

for material_type in material_types:
    if "default_properties" not in material_type:
        continue

    print(f"Validating default_properties of '{material_type['abbreviation']}'")
    try:
        validator.validate(material_type["default_properties"])
    except Exception as e:
        e.add_note(f"When validating default_properties of '{material_type['abbreviation']}'")
        raise
