import shutil
import os
import yaml
import copy
import json

dir = os.path.abspath(os.path.dirname(__file__) + "/../")
data_dir = f"{dir}/data"

out_dir = None
required_field = None
filter_field = None

schema_base = ""


def setup(out_dir_, required_field_, filter_field_):
    global out_dir, required_field, filter_field
    out_dir = f"{dir}/schema/generated/{out_dir_}"
    required_field = required_field_
    filter_field = filter_field_

    # Re-create output directory
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)


type_schemas = {}


def register_type_schema(name, schema):
    type_schemas[name] = schema


def type_schema(type, field_yaml):
    result = type_schemas[type]
    if callable(result):
        result = result(field_yaml)

    return result


uuid_schema = {"type": "string", "format": "uuid"}


def object_ref_schema(object_schema_file):
    return {"$ref": f"{object_schema_file}.schema.json"}


def read_yaml(yaml_file):
    yaml_file = f"{data_dir}/{yaml_file}.yaml"
    return yaml.safe_load(open(os.path.join(data_dir, yaml_file), "r"))


def entity_yaml(source_yaml, class_name):
    return next((item for item in source_yaml["objects"] if item["name"] == class_name))


def enum_schema(yaml, name_item="name"):
    return {
        "type": "string",
        "enum": [item[name_item] for item in yaml if not item.get("deprecated", False)],
    }


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
):
    result = {
        "type": "object",
        "title": yaml["name"],
        "properties": {},
        "required": [],
    }

    if include_inherits is not False:
        result["unevaluatedProperties"] = False

    def is_field_excluded(field_name):
        if "(" in field_name:
            # Exclude "function" fields
            return True

        if (fields_whitelist is not None) and (field_name not in fields_whitelist):
            return True

        if field_name in fields_blacklist:
            return True

        return False

    for field in yaml["fields"]:
        if not field.get(filter_field, True):
            continue

        field_name = field["name"]
        if is_field_excluded(field_name):
            continue

        data = copy.deepcopy(type_schema(field["type"], field))
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

        if field.get(required_field, False):
            result["required"].append(field_name)

    if parent := yaml.get("inherits", None):
        assert include_inherits is not None, f"Entity {yaml['name']} has a parent, please specify whether to include it or not"
        if include_inherits:
            result = recursive_merge(result, type_schema(parent, []))

    all_field_names = set(result["properties"].keys())
    assert len(fields_blacklist - all_field_names) == 0, f"{yaml['name']}: Nonexistent field blacklisted: {fields_blacklist - all_field_names}"
    assert (fields_whitelist is None) or len(fields_whitelist - all_field_names) == 0, f"{yaml['name']}: Nonexistent field whitelisted: {fields_whitelist - all_field_names}"

    # Filter out inherited fields as well
    result["properties"] = dict(filter(lambda item: not is_field_excluded(item[0]), result["properties"].items()))
    result["required"] = list(filter(lambda key: not is_field_excluded(key), result["required"]))

    assert yaml.get(filter_field, False), f"{yaml['name']} is not marked {filter_field}"

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

    with open(f"{out_dir}/{filename}", "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")  # To satisfy precommit autoformatters


def string_schema(yaml):
    result = {"type": "string"}

    if "opt_db_regex" in yaml:
        result["pattern"] = yaml["opt_db_regex"]

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

color_schema = {
    "type": "string",
    "pattern": "^#[a-f0-9]{6}([a-f0-9]{2})?$",
}
register_type_schema("color", color_schema)

register_type_schema("bool", {"type": "boolean"})

timestamp_schema = {
    "type": "number",
    "description": "Unix timestamp (seconds since epoch, UTC)",
}
register_type_schema("timestamp", timestamp_schema)

register_type_schema("Signature", string_schema)
