from mcp_server.data_loader import load_all
from mcp_server.renderer import render_llms_full_txt

_cache: tuple[dict, dict] | None = None

PRIMITIVES = {"string", "int", "float", "bool", "UUID", "date", "datetime", "url", "color"}


def _get_data() -> tuple[dict, dict]:
    global _cache
    if _cache is None:
        _cache = load_all()
    assert _cache is not None
    return _cache


def _find_entity(name: str, entities: dict) -> dict | None:
    for data in entities.values():
        for obj in data.get("objects", []):
            if obj["name"] == name:
                return obj
    return None


def _description(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(v) for v in value)
    return str(value)


def _entity_tags(entity: dict) -> list[str]:
    tags = []
    if entity.get("in_opt_db", False):
        tags.append("DB")
    if entity.get("in_opt", False):
        tags.append("OPT")
    return tags


def _inner_type(field_type: str) -> str:
    return field_type.replace("list(", "").replace("set(", "").rstrip(")")


def _build_entity_enum_map(entities: dict) -> dict[str, str]:
    """Build a mapping from entity name (e.g. 'MaterialType') to enum stem (e.g. 'material_types')."""
    result = {}
    for data in entities.values():
        for obj in data.get("objects", []):
            if "enum_file" in obj:
                stem = obj["enum_file"].removesuffix(".yaml")
                result[obj["name"]] = stem
    return result


def get_tools_guide() -> dict:
    return {
        "tools": [
            {"name": "get_tools_guide", "signature": "get_tools_guide() → dict", "when_to_use": "First call when bootstrapping. Returns this guide.", "example_input": None},
            {"name": "get_overview", "signature": "get_overview() → dict", "when_to_use": "Bird's-eye view of all entities and enums before fetching details.", "example_input": None},
            {"name": "get_entity", "signature": "get_entity(name: str) → dict", "when_to_use": "Full field-level schema for one entity.", "example_input": {"name": "Material"}},
            {"name": "get_enum", "signature": "get_enum(name: str) → dict", "when_to_use": "All values for one enum.", "example_input": {"name": "material_types"}},
            {"name": "get_relationships", "signature": "get_relationships(entity: str) → dict", "when_to_use": "Inheritance and references for one entity.", "example_input": {"entity": "Material"}},
            {"name": "get_examples", "signature": "get_examples(entity: str) → dict", "when_to_use": "Valid example object for test fixtures or understanding valid data.", "example_input": {"entity": "Material"}},
            {"name": "validate_data", "signature": "validate_data(entity: str, data: dict) → dict", "when_to_use": "Check a JSON object against the architecture schema.", "example_input": {"entity": "Material", "data": {"uuid": "550e8400-e29b-41d4-a716-446655440000", "name": "PETG CF Black"}}},
            {"name": "find_discrepancies", "signature": "find_discrepancies(schema: dict) → dict", "when_to_use": "Compare a downstream schema (Drizzle, Pydantic, GraphQL) against the architecture.", "example_input": {"entity": "Material", "fields": [{"name": "uuid", "type": "string"}]}},
            {"name": "get_full_context", "signature": "get_full_context() → str", "when_to_use": "Full architecture as Markdown string — for CI pipelines and headless agents.", "example_input": None},
            {"name": "search", "signature": "search(query: str) → list", "when_to_use": "Full-text search across the entire architecture.", "example_input": {"query": "uuid"}},
        ],
        "recommended_flows": [
            {"scenario": "Verify data against architecture", "steps": ["get_overview()", "get_entity(name)", "validate_data(entity, data)"]},
            {"scenario": "Find discrepancies in a downstream schema", "steps": ["get_overview()", "find_discrepancies(schema)"]},
            {"scenario": "Codegen types for a new service", "steps": ["get_overview()", "get_entity(name)", "get_relationships(name)", "get_examples(name)"]},
            {"scenario": "Onboarding / understand the domain model", "steps": ["get_tools_guide()", "get_overview()", "get_full_context()"]},
            {"scenario": "Data migration", "steps": ["get_entity(name)", "find_discrepancies(current_schema)", "get_examples(name)"]},
        ],
    }


def get_overview() -> dict:
    entities_data, enums_data = _get_data()
    entities = []
    for data in entities_data.values():
        for obj in data.get("objects", []):
            desc = _description(obj.get("description"))
            if len(desc) > 120:
                desc = desc[:117] + "..."
            entities.append(
                {
                    "name": obj["name"],
                    "description": desc,
                    "tags": _entity_tags(obj),
                    "fields_count": len(obj.get("fields", [])),
                }
            )

    enums = []
    for stem, data in enums_data.items():
        active = [i for i in data["items"] if not i.get("deprecated", False)]
        enums.append({"name": stem, "description": "", "values_count": len(active)})

    return {"entities": entities, "enums": enums}


def get_entity(name: str) -> dict:
    entities, _ = _get_data()
    entity = _find_entity(name, entities)
    if entity is None:
        return {"error": f"Entity '{name}' not found. Call get_overview() to see all entities."}

    return {
        "name": entity["name"],
        "description": _description(entity.get("description")),
        "tags": _entity_tags(entity),
        "inherits": entity.get("inherits"),
        "fields": [
            {
                "name": f["name"],
                "type": f.get("type"),
                "primary_key": f.get("primary_key", False),
                "required_in_db": f.get("required_in_opt_db", False),
                "in_db": f.get("in_opt_db", True),
                "in_opt": f.get("in_opt", False),
                "max_length": f.get("max_length"),
                "example": f.get("example"),
                "description": _description(f.get("description")),
            }
            for f in entity.get("fields", [])
        ],
    }


def get_enum(name: str) -> dict:
    _, enums = _get_data()
    if name not in enums:
        return {"error": f"Enum '{name}' not found. Call get_overview() to see all enums."}
    items = [{k: v for k, v in item.items() if k != "deprecated"} for item in enums[name]["items"] if not item.get("deprecated", False)]
    return {"name": name, "values": items}


def get_relationships(entity: str) -> dict:
    entities, _ = _get_data()
    ent = _find_entity(entity, entities)
    if ent is None:
        return {"error": f"Entity '{entity}' not found."}

    references = []
    for field in ent.get("fields", []):
        inner = _inner_type(str(field.get("type", "")))
        if inner and inner not in PRIMITIVES and inner[0].isupper():
            references.append({"field": field["name"], "target": inner})

    referenced_by = []
    for data in entities.values():
        for obj in data.get("objects", []):
            if obj["name"] == entity:
                continue
            for field in obj.get("fields", []):
                if _inner_type(str(field.get("type", ""))) == entity:
                    referenced_by.append({"entity": obj["name"], "field": field["name"]})

    return {
        "entity": entity,
        "inherits": ent.get("inherits"),
        "references": references,
        "referenced_by": referenced_by,
    }


def get_examples(entity: str) -> dict:
    entities, _ = _get_data()
    ent = _find_entity(entity, entities)
    if ent is None:
        return {"error": f"Entity '{entity}' not found."}
    example = {f["name"]: f["example"] for f in ent.get("fields", []) if "example" in f}
    return {"entity": entity, "example": example}


def get_full_context() -> str:
    entities, enums = _get_data()
    return render_llms_full_txt(entities, enums)


def search(query: str) -> list:
    entities, enums = _get_data()
    q = query.lower()
    results = []

    for data in entities.values():
        for entity in data.get("objects", []):
            if q in entity["name"].lower():
                results.append({"type": "entity", "entity": entity["name"], "field": None, "match_context": f"Entity name: {entity['name']}"})
            if q in _description(entity.get("description")).lower():
                results.append({"type": "entity", "entity": entity["name"], "field": None, "match_context": f"Entity description: {_description(entity.get('description'))[:100]}"})
            for field in entity.get("fields", []):
                if q in field["name"].lower():
                    results.append({"type": "field", "entity": entity["name"], "field": field["name"], "match_context": f"Field name: {field['name']} (type: {field.get('type', '')})"})
                if q in _description(field.get("description")).lower():
                    results.append({"type": "field", "entity": entity["name"], "field": field["name"], "match_context": f"Field description: {_description(field.get('description'))[:100]}"})

    for stem, data in enums.items():
        for item in data["items"]:
            item_str = " ".join(str(v) for v in item.values()).lower()
            if q in item_str:
                results.append({"type": "enum_value", "entity": stem, "field": item.get("name") or item.get("abbreviation"), "match_context": f"Enum {stem}: {item}"})

    return results


def validate_data(entity: str, data: dict) -> dict:
    entities, enums = _get_data()
    ent = _find_entity(entity, entities)
    if ent is None:
        return {"valid": False, "errors": [{"field": "_entity", "issue": f"Entity '{entity}' not found", "expected": "valid entity name", "got": entity}]}

    errors = []
    fields_by_name = {f["name"]: f for f in ent.get("fields", [])}

    for field_name, field_def in fields_by_name.items():
        if field_def.get("required_in_opt_db", False) and field_name not in data:
            errors.append({"field": field_name, "issue": "required field missing", "expected": f"'{field_name}' to be present", "got": "absent"})

    for field_name, value in data.items():
        if field_name not in fields_by_name:
            continue
        field_def = fields_by_name[field_name]

        max_length = field_def.get("max_length")
        if max_length and isinstance(value, str) and len(value) > max_length:
            errors.append({"field": field_name, "issue": "value exceeds max_length", "expected": f"<= {max_length} chars", "got": f"{len(value)} chars"})

        inner = _inner_type(str(field_def.get("type", "")))
        entity_enum_map = _build_entity_enum_map(entities)
        enum_stem = entity_enum_map.get(inner)
        if enum_stem and enum_stem in enums:
            valid_values = {item.get("name") or item.get("abbreviation", "") for item in enums[enum_stem]["items"] if not item.get("deprecated", False)}
            if isinstance(value, str) and value not in valid_values:
                sample = sorted(valid_values)[:8]
                errors.append({"field": field_name, "issue": "value not in enum", "expected": f"one of {sample}{'...' if len(valid_values) > 8 else ''}", "got": value})

    return {"valid": len(errors) == 0, "errors": errors}


def find_discrepancies(schema: dict) -> dict:
    entities, _ = _get_data()
    entity_name = schema.get("entity", "")
    provided = {f["name"]: f for f in schema.get("fields", [])}

    ent = _find_entity(entity_name, entities)
    if ent is None:
        return {"error": f"Entity '{entity_name}' not found."}

    arch = {f["name"]: f for f in ent.get("fields", [])}

    missing_fields = [{"name": n, "type": f.get("type", ""), "description": _description(f.get("description"))} for n, f in arch.items() if n not in provided]

    type_mismatches = []
    for name, pf in provided.items():
        if name in arch:
            arch_type = arch[name].get("type", "")
            prov_type = pf.get("type", "")
            if arch_type and prov_type and arch_type.lower() != prov_type.lower():
                type_mismatches.append({"field": name, "architecture_type": arch_type, "provided_type": prov_type})

    extra_fields = [n for n in provided if n not in arch]

    required_missing = [n for n, f in arch.items() if f.get("required_in_opt_db", False) and n not in provided]

    return {
        "missing_fields": missing_fields,
        "type_mismatches": type_mismatches,
        "extra_fields": extra_fields,
        "required_missing": required_missing,
    }
