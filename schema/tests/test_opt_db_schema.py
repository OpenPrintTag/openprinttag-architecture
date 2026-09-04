from pathlib import Path

import yaml
from schema_test_common import get_validator, make_registry

script_dir = Path(__file__).parent
schema_dir = script_dir / ".." / "generated" / "opt_db_schema"
tests_dir = script_dir / "opt_db_schema"

registry = make_registry(schema_dir)

for f in tests_dir.glob("*.yaml"):
    schema_name = f.with_suffix(".schema.json").name

    print(f"Testing {f.name} against {schema_name}")

    validator = get_validator(registry, schema_name)
    validator.validate(yaml.safe_load(f.read_bytes()))
