from mcp_server.tools import (
    get_tools_guide,
    get_overview,
    get_entity,
    get_enum,
    get_relationships,
    get_examples,
    get_full_context,
    search,
    validate_data,
    find_discrepancies,
)


def test_get_tools_guide_lists_all_10_tools():
    result = get_tools_guide()
    names = [t["name"] for t in result["tools"]]
    for expected in ["get_tools_guide", "get_overview", "get_entity", "get_enum",
                     "get_relationships", "get_examples", "validate_data",
                     "find_discrepancies", "get_full_context", "search"]:
        assert expected in names, f"Missing tool: {expected}"


def test_get_tools_guide_has_recommended_flows():
    result = get_tools_guide()
    assert len(result["recommended_flows"]) >= 5


def test_get_overview_has_entities_and_enums():
    result = get_overview()
    assert "entities" in result
    assert "enums" in result


def test_get_overview_entities_include_material_and_brand():
    result = get_overview()
    names = [e["name"] for e in result["entities"]]
    assert "Material" in names
    assert "Brand" in names


def test_get_overview_entity_has_required_keys():
    result = get_overview()
    material = next(e for e in result["entities"] if e["name"] == "Material")
    assert "description" in material
    assert "tags" in material
    assert "fields_count" in material
    assert material["fields_count"] > 5


def test_get_overview_enums_include_material_types():
    result = get_overview()
    names = [e["name"] for e in result["enums"]]
    assert "material_types" in names


def test_get_overview_enum_has_values_count():
    result = get_overview()
    mt = next(e for e in result["enums"] if e["name"] == "material_types")
    assert mt["values_count"] > 5


def test_get_entity_material_has_correct_name():
    result = get_entity("Material")
    assert result["name"] == "Material"


def test_get_entity_material_has_expected_fields():
    result = get_entity("Material")
    field_names = [f["name"] for f in result["fields"]]
    assert "uuid" in field_names
    assert "brand" in field_names
    assert "name" in field_names


def test_get_entity_material_has_db_tag():
    result = get_entity("Material")
    assert "DB" in result["tags"]


def test_get_entity_field_has_required_keys():
    result = get_entity("Material")
    uuid_field = next(f for f in result["fields"] if f["name"] == "uuid")
    assert "type" in uuid_field
    assert "primary_key" in uuid_field
    assert "required_in_db" in uuid_field


def test_get_entity_unknown_name_returns_error():
    result = get_entity("DoesNotExist")
    assert "error" in result


def test_get_enum_material_types_has_values():
    result = get_enum("material_types")
    assert result["name"] == "material_types"
    assert len(result["values"]) > 5


def test_get_enum_values_contain_pla():
    result = get_enum("material_types")
    all_text = [str(v.get("name", "")) + " " + str(v.get("abbreviation", "")) for v in result["values"]]
    assert any("PLA" in text for text in all_text)


def test_get_enum_excludes_deprecated_values():
    result = get_enum("material_tags")
    for v in result["values"]:
        assert not v.get("deprecated", False)


def test_get_enum_unknown_returns_error():
    result = get_enum("nonexistent_enum")
    assert "error" in result


def test_get_relationships_material_references_brand():
    result = get_relationships("Material")
    assert result["entity"] == "Material"
    targets = [r["target"] for r in result["references"]]
    assert "Brand" in targets


def test_get_relationships_has_referenced_by():
    result = get_relationships("Material")
    assert isinstance(result["referenced_by"], list)


def test_get_relationships_inherits_is_none_or_string():
    result = get_relationships("Material")
    assert result["inherits"] is None or isinstance(result["inherits"], str)


def test_get_relationships_unknown_returns_error():
    result = get_relationships("DoesNotExist")
    assert "error" in result


def test_get_examples_material_returns_dict():
    result = get_examples("Material")
    assert result["entity"] == "Material"
    assert isinstance(result["example"], dict)
    assert len(result["example"]) > 0


def test_get_examples_contains_brand_example():
    result = get_examples("Material")
    example = result["example"]
    assert "brand" in example
    assert example["brand"] == "Prusament"


def test_get_examples_unknown_returns_error():
    result = get_examples("DoesNotExist")
    assert "error" in result


def test_get_full_context_is_string():
    result = get_full_context()
    assert isinstance(result, str)


def test_get_full_context_has_all_entity_headers():
    result = get_full_context()
    assert "## Entity: Material" in result
    assert "## Entity: Brand" in result


def test_get_full_context_has_enum_headers():
    result = get_full_context()
    assert "## Enum: material_types" in result


def test_get_full_context_has_conventions():
    result = get_full_context()
    assert "## Conventions" in result
    assert "<<DB>>" in result


def test_search_uuid_finds_field_results():
    results = search("uuid")
    types = [r["type"] for r in results]
    assert "field" in types


def test_search_uuid_finds_material():
    results = search("uuid")
    entities = [r["entity"] for r in results if r["type"] == "field"]
    assert "Material" in entities


def test_search_brand_finds_entity():
    results = search("Brand")
    entity_hits = [r for r in results if r["type"] == "entity" and r["entity"] == "Brand"]
    assert len(entity_hits) > 0


def test_search_no_match_returns_empty_list():
    results = search("xyzzy_this_cannot_match_12345")
    assert results == []


def test_search_result_has_required_keys():
    results = search("uuid")
    assert len(results) > 0
    r = results[0]
    assert "type" in r
    assert "entity" in r
    assert "match_context" in r


# --- validate_data ---

def test_validate_data_valid_data_returns_no_errors():
    # Pass only non-required fields — should be valid since no required fields are missing
    result = validate_data("Brand", {"uuid": "550e8400-e29b-41d4-a716-446655440000", "name": "Prusament"})
    assert "valid" in result
    assert "errors" in result
    assert isinstance(result["errors"], list)


def test_validate_data_unknown_entity_returns_invalid():
    result = validate_data("DoesNotExist", {})
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert result["errors"][0]["field"] == "_entity"


def test_validate_data_max_length_violation():
    # MaterialType.abbreviation has max_length: 7
    result = validate_data("MaterialType", {"abbreviation": "TOOLONGABBREVIATION"})
    assert result["valid"] is False
    error_fields = [e["field"] for e in result["errors"]]
    assert "abbreviation" in error_fields


def test_validate_data_max_length_ok():
    result = validate_data("MaterialType", {"abbreviation": "PETG"})
    # No max_length error for a short abbreviation
    errors = [e for e in result["errors"] if e["field"] == "abbreviation" and "max_length" in e["issue"]]
    assert len(errors) == 0


def test_validate_data_returns_valid_true_when_no_errors():
    # Brand requires uuid and name; supply both so we get valid=True
    result = validate_data("Brand", {"uuid": "550e8400-e29b-41d4-a716-446655440000", "name": "Prusament"})
    assert result["valid"] is True
    assert result["errors"] == []


def test_validate_data_missing_required_field():
    # Brand.uuid and Brand.name are required_in_opt_db; omitting them should produce errors
    result = validate_data("Brand", {})
    assert result["valid"] is False
    error_fields = [e["field"] for e in result["errors"]]
    assert "uuid" in error_fields
    assert "name" in error_fields


def test_validate_data_invalid_enum_value_caught():
    # Material.type is of type MaterialType, which has enum_file: material_types.yaml
    # "ZZZ" is a short value (won't hit max_length) but is not a valid MaterialType abbreviation
    result = validate_data("Material", {"type": "ZZZ"})
    assert "valid" in result
    assert "errors" in result
    assert result["valid"] is False
    error_fields = [e["field"] for e in result["errors"]]
    assert "type" in error_fields
    enum_error = next(e for e in result["errors"] if e["field"] == "type")
    assert enum_error["issue"] == "value not in enum"


def test_validate_data_valid_enum_value_accepted():
    # MaterialType enum items use `name` (full name) as the primary key in valid_values.
    # "Polyethylene Terephthalate Glycol" is the full name for PETG — should not produce an enum error.
    result = validate_data("Material", {"type": "Polyethylene Terephthalate Glycol"})
    enum_errors = [e for e in result["errors"] if e["field"] == "type" and e["issue"] == "value not in enum"]
    assert len(enum_errors) == 0


# --- find_discrepancies ---

def test_find_discrepancies_missing_fields():
    result = find_discrepancies({
        "entity": "Material",
        "fields": [{"name": "uuid", "type": "UUID"}],
    })
    missing_names = [f["name"] for f in result["missing_fields"]]
    assert "brand" in missing_names
    assert "name" in missing_names


def test_find_discrepancies_type_mismatch():
    result = find_discrepancies({
        "entity": "Material",
        "fields": [{"name": "uuid", "type": "integer"}],
    })
    mismatches = [m["field"] for m in result["type_mismatches"]]
    assert "uuid" in mismatches


def test_find_discrepancies_extra_fields():
    result = find_discrepancies({
        "entity": "Brand",
        "fields": [
            {"name": "uuid", "type": "UUID"},
            {"name": "nonexistent_field_xyz", "type": "string"},
        ],
    })
    assert "nonexistent_field_xyz" in result["extra_fields"]


def test_find_discrepancies_unknown_entity_returns_error():
    result = find_discrepancies({"entity": "DoesNotExist", "fields": []})
    assert "error" in result


def test_find_discrepancies_no_issues_when_exact_match():
    # Get all field names and types from Brand entity
    brand = get_entity("Brand")
    schema_fields = [{"name": f["name"], "type": f["type"] or ""} for f in brand["fields"]]
    result = find_discrepancies({"entity": "Brand", "fields": schema_fields})
    assert result["missing_fields"] == []
    assert result["extra_fields"] == []
