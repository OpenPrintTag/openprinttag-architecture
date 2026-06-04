import pathlib
import os
import pytest
from mcp_server.data_loader import load_all, get_data_dir


def test_get_data_dir_resolves_to_existing_path():
    data_dir = get_data_dir()
    assert data_dir.exists()
    assert (data_dir / "materials.yaml").exists()


def test_get_data_dir_uses_env_var(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    monkeypatch.setenv("ARCH_REPO_PATH", str(tmp_path))
    data_dir = get_data_dir()
    assert str(tmp_path) in str(data_dir)


def test_load_all_finds_entity_yamls():
    entity_yamls, _ = load_all()
    assert "materials" in entity_yamls
    assert "brands" in entity_yamls
    assert "packaging" in entity_yamls


def test_load_all_entity_has_objects():
    entity_yamls, _ = load_all()
    assert "objects" in entity_yamls["materials"]
    assert isinstance(entity_yamls["materials"]["objects"], list)
    assert len(entity_yamls["materials"]["objects"]) > 0


def test_load_all_finds_enum_yamls():
    _, enum_yamls = load_all()
    assert "material_types" in enum_yamls
    assert "material_tags" in enum_yamls


def test_load_all_enum_has_items():
    _, enum_yamls = load_all()
    assert "items" in enum_yamls["material_types"]
    assert isinstance(enum_yamls["material_types"]["items"], list)
    assert len(enum_yamls["material_types"]["items"]) > 0


def test_load_all_custom_data_dir(tmp_path):
    (tmp_path / "things.yaml").write_text("objects:\n  - name: Thing\n    fields: []")
    (tmp_path / "colors.yaml").write_text("- key: 1\n  name: red")
    entity_yamls, enum_yamls = load_all(data_dir=tmp_path)
    assert "things" in entity_yamls
    assert "colors" in enum_yamls
