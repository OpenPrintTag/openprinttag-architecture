from datetime import datetime, timezone

REPO_URL = "https://github.com/OpenPrintTag/openprinttag-architecture"
SITE_URL = "https://arch.openprinttag.org"
PRIMITIVES = {"string", "int", "float", "bool", "UUID", "date", "datetime", "url", "color"}


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


def _field_relationships(entity: dict) -> str:
    refs = []
    for field in entity.get("fields", []):
        ft = str(field.get("type", ""))
        inner = ft.replace("list(", "").replace("set(", "").rstrip(")")
        if inner and inner not in PRIMITIVES and inner[0].isupper():
            refs.append(f"`{field['name']}` → {inner}")
    return ", ".join(refs) if refs else "none"


def _render_entity_section(entity: dict) -> str:
    name = entity["name"]
    tags = _entity_tags(entity)
    desc = _description(entity.get("description"))

    lines = [f"## Entity: {name}"]
    if tags:
        lines.append(f"> Used in: {', '.join(tags)}")
    if desc:
        lines.append("")
        lines.append(desc)
    lines.append("")
    lines.append("| Field | Type | Required (DB) | Example | Description |")
    lines.append("|-------|------|:---:|---------|-------------|")
    for field in entity.get("fields", []):
        pk = "*" if field.get("primary_key", False) else ""
        req = "✓" if field.get("required_in_opt_db", False) else ""
        example = str(field.get("example", ""))
        desc_f = _description(field.get("description"))
        lines.append(f"| {pk}{field['name']} | {field.get('type', '')} | {req} | {example} | {desc_f} |")
    lines.append("")
    lines.append(f"**Relationships:** {_field_relationships(entity)}")
    return "\n".join(lines)


def _render_enum_section(stem: str, data: dict) -> str:
    items = [i for i in data["items"] if not i.get("deprecated", False)]
    if not items:
        return ""
    first = items[0]

    has_key = "key" in first
    has_abbr = "abbreviation" in first
    has_name = "name" in first
    has_display = "display_name" in first
    has_desc = "description" in first

    headers = (["Key"] if has_key else []) + (["Abbreviation"] if has_abbr else []) + \
              (["Name"] if has_name else []) + (["Display Name"] if has_display else []) + \
              (["Description"] if has_desc else [])

    lines = [f"## Enum: {stem}", ""]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for item in items:
        row = []
        if has_key:
            row.append(str(item.get("key", "")))
        if has_abbr:
            row.append(f"`{item.get('abbreviation', '')}`")
        if has_name:
            row.append(f"`{item.get('name', '')}`")
        if has_display:
            row.append(str(item.get("display_name", "")))
        if has_desc:
            row.append(_description(item.get("description")))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_llms_txt(entity_yamls: dict, enum_yamls: dict) -> str:
    entity_page_map = {"materials": "materials", "brands": "brands", "packaging": "packaging"}

    lines = [
        "# OpenPrintTag Architecture",
        "> Shared domain ontology for the OpenPrintTag NFC Data Format and Database.",
        "> Defines Materials, Brands, Packaging and related enums used across all services.",
        f"> Source: {REPO_URL}",
        "",
        "## Overview",
        f"- [README]({SITE_URL}/#/README): Architecture introduction and conventions",
        "",
        "## Entities",
    ]
    for stem, data in entity_yamls.items():
        names = [obj["name"] for obj in data.get("objects", [])]
        page = entity_page_map.get(stem, stem)
        lines.append(f"- [{stem.replace('_', ' ').title()}]({SITE_URL}/#/{page}): {', '.join(names)}")

    lines += [
        "",
        "## Optional",
        f"- [Full context]({SITE_URL}/llms-full.txt): Complete entity and enum definitions",
        f"- [JSON Schemas]({SITE_URL}/schema/): Per-entity JSON Schema files",
    ]
    return "\n".join(lines) + "\n"


def render_llms_full_txt(entity_yamls: dict, enum_yamls: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parts = [
        "# OpenPrintTag Architecture — Full Context",
        f"> Generated: {now}",
        f"> Source: {REPO_URL}",
        "",
        "## Conventions",
        "- `<<DB>>` = stored in the OpenPrintTag Database",
        "- `<<OPT>>` = encoded in the NFC tag",
        "- `list(Type)` = ordered relation; `set(Type)` = unordered",
        "- `*` prefix = primary key field",
    ]

    for data in entity_yamls.values():
        for entity in data.get("objects", []):
            parts.append("---")
            parts.append(_render_entity_section(entity))

    for stem, data in enum_yamls.items():
        section = _render_enum_section(stem, data)
        if section:
            parts.append("---")
            parts.append(section)

    return "\n\n".join(parts) + "\n"
