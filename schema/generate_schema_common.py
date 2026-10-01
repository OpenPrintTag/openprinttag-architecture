import copy
import json
import os
import shutil
from collections.abc import Callable

import yaml

dir = os.path.abspath(os.path.dirname(__file__) + "/../")
data_dir = f"{dir}/data"

_out_dir = None
_schema_name = None

schema_base = ""


def setup(out_dir: str, *, schema_name: str | None = None):
    global _out_dir, _schema_name
    _schema_name = schema_name or out_dir
    _out_dir = f"{dir}/schema/generated/{out_dir}"

    # Re-create output directory
    shutil.rmtree(_out_dir, ignore_errors=True)
    os.makedirs(_out_dir)


type_schemas = {}


def resolve_target_specific_field(data, default_value, *, schema_name: str):
    if data is None:
        return default_value

    elif isinstance(data, dict):
        if (r := data.get(schema_name, None)) is not None:
            return r
        else:
            return data.get("default", default_value)

    else:
        return data


def register_type_schema(name, schema):
    type_schemas[name] = schema


def type_schema(type, field_yaml):
    result = type_schemas[type]
    if callable(result):
        result = result(field_yaml)

    return result


uuid_schema = {"type": "string", "format": "uuid"}


def object_ref_schema(ref, entity_name: str | None = None, *, is_filename: bool = True):
    if is_filename:
        ref += ".schema.json"

    result = {"$ref": ref}

    if entity_name:
        result["title"] = entity_name

    return result


def read_yaml(yaml_file):
    yaml_file = f"{data_dir}/{yaml_file}.yaml"
    return yaml.safe_load(open(os.path.join(data_dir, yaml_file), "r"))


def entity_yaml(source_yaml, class_name):
    return next((item for item in source_yaml["objects"] if item["name"] == class_name))


def enum_schema(yaml, name_item="name", entity_name: str | None = None):
    result = {
        "type": "string",
        "enum": [item[name_item] for item in yaml if not item.get("deprecated", False)],
    }

    if entity_name:
        result["title"] = entity_name

    return result


def array_schema(entity_schema):
    return {
        "type": "array",
        "items": entity_schema,
    }


def entity_schema(
    yaml,
    include_inherits: bool | None = None,
    fields_whitelist: set[str] | None = None,
    fields_blacklist: set[str] = set(),
    schema_func: Callable = type_schema,
    schema_name: str | None = None,
    allow_unevaluated_properties: bool | None = None,
):
    result = {
        "type": "object",
        "title": yaml["name"],
        "properties": {},
        "required": [],
        "x-recommended": [],
    }

    if schema_name is None:
        schema_name = _schema_name

    if allow_unevaluated_properties is not None:
        result["unevaluatedProperties"] = allow_unevaluated_properties
    elif include_inherits is not False:
        result["unevaluatedProperties"] = False

    def is_field_excluded(field_name):
        if "(" in field_name:
            # Exclude "function" fields
            return True

        if (fields_whitelist is not None) and (field_name not in fields_whitelist):
            return True

        if field_name in fields_blacklist:  # noqa: SIM103
            return True

        return False

    all_field_names = set()
    for field in yaml["fields"]:
        # Fields used_in is opt-out
        if not resolve_target_specific_field(field.get("used_in"), True, schema_name=schema_name):
            continue

        field_name = field["name"]

        # Consider excluded fields in all_field_names
        all_field_names.add(field_name)

        if is_field_excluded(field_name):
            continue

        data = copy.deepcopy(schema_func(field["type"], field))
        desc = ""

        if unit := field.get("unit"):
            data["x-unit"] = unit

        # Do not copy over examples for references, they do not make sense (for example Brand UUID example "Prusament")
        if (example := field.get("example")) and (data.get("format") != "uuid") and ("$ref" not in data):
            data["x-example"] = example

        if "description" in field:
            desc_val = field["description"]
            if isinstance(desc_val, list):
                desc_val = "\n".join(desc_val)

            desc += "\n"
            desc += desc_val

        desc = desc.strip()
        if len(desc):
            data["description"] = desc

        result["properties"][field_name] = data

        match resolve_target_specific_field(field.get("required"), False, schema_name=schema_name):
            case True:
                result["required"].append(field_name)

            case "recommended":
                result["x-recommended"].append(field_name)

    if parent := yaml.get("inherits", None):
        assert include_inherits is not None, f"Entity {yaml['name']} has a parent, please specify whether to include it or not"
        if include_inherits:
            result = recursive_merge(result, schema_func(parent, []))

    # Also consider field names from parent in all_field_names
    all_field_names |= result["properties"].keys()

    assert len(fields_blacklist - all_field_names) == 0, f"{yaml['name']}: Nonexistent field blacklisted: {fields_blacklist - all_field_names}"
    assert (fields_whitelist is None) or len(fields_whitelist - all_field_names) == 0, f"{yaml['name']}: Nonexistent field whitelisted: {fields_whitelist - all_field_names}"

    # Filter out inherited fields as well
    result["properties"] = dict(filter(lambda item: not is_field_excluded(item[0]), result["properties"].items()))
    result["required"] = list(filter(lambda key: not is_field_excluded(key), result["required"]))
    result["x-recommended"] = list(filter(lambda key: not is_field_excluded(key), result["x-recommended"]))

    # Entity used_in is opt-in
    assert resolve_target_specific_field(yaml.get("used_in"), False, schema_name=schema_name), f"{yaml['name']} is missing used_in: {schema_name}"

    return result


def recursive_merge(a, b):
    if a is None:
        return b

    elif isinstance(a, dict) and isinstance(b, dict):
        result = copy.deepcopy(a)
        for key, value in b.items():
            result[key] = recursive_merge(result.get(key), value)

        return result

    elif isinstance(a, list) and isinstance(b, list):
        result = copy.deepcopy(a)
        for value in b:
            result.append(value)

        return result

    else:
        return a


def generate_schema_file(basename, data, extra_data=None):
    filename = f"{basename}.schema.json"
    print(f"Generating {filename}")

    result = {
        "$id": f"{schema_base}/{basename}",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
    }

    result = recursive_merge(result, data)
    result = recursive_merge(result, extra_data)

    with open(f"{_out_dir}/{filename}", "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")  # To satisfy precommit autoformatters


def string_schema(yaml):
    result = {"type": "string"}

    if "opt_db_regex" in yaml:
        result["pattern"] = yaml["opt_db_regex"]

    if "max_length" in yaml:
        result["maxLength"] = yaml["max_length"]

    if "min_length" in yaml:
        result["minLength"] = yaml["min_length"]

    return result


register_type_schema("string", string_schema)
register_type_schema("set(string)", lambda yaml: array_schema(string_schema(yaml)))

register_type_schema("bytes", string_schema)


def number_schema(yaml):
    result = {"type": "number"}

    if "min" in yaml:
        result["minimum"] = yaml["min"]

    if "max" in yaml:
        result["maximum"] = yaml["max"]

    return result


def uint_schema(yaml):
    yaml["min"] = 0
    number_schema(yaml)


register_type_schema("number", number_schema)
register_type_schema("int", number_schema)
register_type_schema("uint", uint_schema)

register_type_schema("UUID", uuid_schema)

color_rgba_schema = {
    "type": "string",
    "pattern": "^#[a-f0-9]{6}([a-f0-9]{2})?$",
}
register_type_schema("color_rgba", color_rgba_schema)

color_lab_schema = {
    "type": "array",
    "prefixItems": [
        {"type": "number", "minimum": 0, "maximum": 100},
        {"type": "number", "minimum": -150, "maximum": 150},
        {"type": "number", "minimum": -150, "maximum": 150},
    ],
    "items": False,
    "minItems": 3,
    "maxItems": 3,
}
register_type_schema("color_lab", color_lab_schema)

register_type_schema("bool", {"type": "boolean"})

timestamp_schema = {
    "type": "number",
    "description": "Unix timestamp (seconds since epoch, UTC)",
}
register_type_schema("timestamp", timestamp_schema)
