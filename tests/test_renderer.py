import pytest
from mcp_server.data_loader import load_all
from mcp_server.renderer import render_llms_txt, render_llms_full_txt


@pytest.fixture(scope="module")
def data():
    return load_all()


def test_render_llms_txt_starts_with_h1(data):
    entity_yamls, enum_yamls = data
    result = render_llms_txt(entity_yamls, enum_yamls)
    assert result.startswith("# OpenPrintTag Architecture")


def test_render_llms_txt_has_optional_section_with_full_context_link(data):
    entity_yamls, enum_yamls = data
    result = render_llms_txt(entity_yamls, enum_yamls)
    assert "llms-full.txt" in result
    assert "## Optional" in result


def test_render_llms_txt_lists_entity_files(data):
    entity_yamls, enum_yamls = data
    result = render_llms_txt(entity_yamls, enum_yamls)
    assert "materials" in result.lower()
    assert "brands" in result.lower()


def test_render_llms_txt_under_5kb(data):
    entity_yamls, enum_yamls = data
    result = render_llms_txt(entity_yamls, enum_yamls)
    assert len(result.encode("utf-8")) < 5 * 1024, f"llms.txt is {len(result.encode())} bytes, must be < 5KB"


def test_render_llms_full_txt_has_conventions(data):
    entity_yamls, enum_yamls = data
    result = render_llms_full_txt(entity_yamls, enum_yamls)
    assert "## Conventions" in result
    assert "<<DB>>" in result
    assert "<<OPT>>" in result


def test_render_llms_full_txt_has_all_entities(data):
    entity_yamls, enum_yamls = data
    result = render_llms_full_txt(entity_yamls, enum_yamls)
    assert "## Entity: Material" in result
    assert "## Entity: Brand" in result


def test_render_llms_full_txt_entity_has_field_table(data):
    entity_yamls, enum_yamls = data
    result = render_llms_full_txt(entity_yamls, enum_yamls)
    assert "| Field | Type |" in result
    assert "uuid" in result


def test_render_llms_full_txt_has_enums(data):
    entity_yamls, enum_yamls = data
    result = render_llms_full_txt(entity_yamls, enum_yamls)
    assert "## Enum: material_types" in result


def test_render_llms_full_txt_entity_has_relationships(data):
    entity_yamls, enum_yamls = data
    result = render_llms_full_txt(entity_yamls, enum_yamls)
    assert "**Relationships:**" in result


def test_render_llms_full_txt_has_generated_date(data):
    entity_yamls, enum_yamls = data
    result = render_llms_full_txt(entity_yamls, enum_yamls)
    assert "> Generated:" in result
