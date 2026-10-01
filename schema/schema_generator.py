import json
import re
import shutil
import typing
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import generate_schema_common as old
import yaml

root_dir = Path(__file__).parent.parent
data_dir = root_dir / "data"

Schema = dict
YamlData = dict


@dataclass
class SchemaGeneratorArgs:
    field_yaml: YamlData


class SchemaGenerator:
    _schema_name: str
    _out_dir: Path
    _entity_yamls: dict[str, YamlData]
    _known_type_schemas: dict[str, Schema | Callable[[SchemaGeneratorArgs], Schema]]
    _source_files: dict[Path, YamlData]

    def __init__(self, *, out_dir: Path, schema_name: str | None = None):
        self._schema_name = schema_name or Path(out_dir).name
        self._out_dir = root_dir / "schema" / "generated" / out_dir

        # Re-create output directory
        shutil.rmtree(self._out_dir, ignore_errors=True)
        self._out_dir.mkdir(parents=True, exist_ok=True)

        self._entity_yamls = {}
        self._source_files = {}

        self._known_type_schemas = {
            "int": lambda args: old.number_schema(args.field_yaml),
            "number": lambda args: old.number_schema(args.field_yaml),
            "UUID": lambda args: old.uuid_schema,
            "string": lambda args: old.string_schema(args.field_yaml),
            "bool": lambda args: {"type": "boolean"},
            "timestamp": lambda args: old.timestamp_schema,
            "color_rgba": lambda args: old.color_rgba_schema,
            "color_lab": lambda args: old.color_lab_schema,
        }

    def add_source_file(self, file: Path):
        file = (data_dir / file).resolve()
        if file in self._source_files:
            return

        file_yaml = yaml.safe_load(file.read_text())
        self._source_files[file] = file_yaml

        for entity_yaml in file_yaml["objects"]:
            entity_name = entity_yaml["name"]
            assert entity_name not in self._entity_yamls
            self._entity_yamls[entity_name] = entity_yaml

    def add_known_type_schema(self, schema: Schema):
        type_name = schema["title"]
        assert len(type_name) > 0
        assert type_name not in self._known_type_schemas
        self._known_type_schemas[type_name] = schema

    def known_type_schema(self, type_name: str) -> Schema | None:
        return self._known_type_schemas.get(type_name, None)

    def export_file(self, basename: str, schema: Schema):
        result = {
            "$id": f"/{basename}",
            "$schema": "https://json-schema.org/draft/2020-12/schema",
        }

        result = old.recursive_merge(result, schema)
        result_json = json.dumps(result, indent=2) + "\n"
        (self._out_dir / f"{basename}.schema.json").write_text(result_json)

    # Schema generator functions

    def recursive_merge(self, *args):
        iterator = iter(args)
        result = next(iterator)
        for b in iterator:
            result = old.recursive_merge(result, b)

        return result

    def known_type(self, type_name: str) -> Schema:
        return self._known_type_schemas[type_name]

    def entity(
        self,
        entity_name: str,
        *,
        include_inherits: bool | None = None,
        fields_whitelist: set[str] | None = None,
        fields_blacklist: set[str] = set(),
        type_schemas: dict[str, Schema] = dict(),
        allow_unevaluated_properties: bool | None = None,
        strip_metadata: bool = False,
    ):
        def _schema_func(type_name: str, field_yaml: typing.Any):
            if (r := type_schemas.get(type_name)) is not None:  # noqa: SIM114
                return r

            elif (r := self._known_type_schemas.get(type_name)) is not None:
                if isinstance(r, Schema):
                    return r
                else:
                    return r(
                        SchemaGeneratorArgs(
                            field_yaml=field_yaml,
                        )
                    )

            elif (m := re.fullmatch(r"(set|list)\((.+)\)", type_name)) is not None:
                return old.array_schema(_schema_func(m.group(2), field_yaml))

            else:
                raise Exception(f'Unknown type "{type_name}"')

        result = old.entity_schema(
            self._entity_yamls[entity_name],
            include_inherits=include_inherits,
            fields_whitelist=fields_whitelist,
            fields_blacklist=fields_blacklist,
            schema_func=_schema_func,
            schema_name=self._schema_name,
            allow_unevaluated_properties=allow_unevaluated_properties,
        )

        if strip_metadata:
            for key in ("type", "title", "unevaluatedProperties"):
                result.pop(key, None)

        return result

    def enum(self, entity_name: str, yaml_file: Path, key_field: str = "key"):
        return old.enum_schema(
            yaml.safe_load((data_dir / yaml_file).read_text()),
            name_item=key_field,
            entity_name=entity_name,
        )

    def object_ref(self, entity_name: str | None, ref: str, *, is_filename: bool = True):
        return old.object_ref_schema(ref, entity_name=entity_name, is_filename=is_filename)
