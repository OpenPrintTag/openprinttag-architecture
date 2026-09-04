from pathlib import Path

import yaml
from schema_test_common import get_validator, make_registry

script_dir = Path(__file__).parent
schema_dir = script_dir / ".." / "generated" / "opt_db_schema"
data_dir = script_dir / ".." / ".." / "data"

registry = make_registry(schema_dir)
validator = get_validator(registry, "fff_material_properties.schema.json")

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
