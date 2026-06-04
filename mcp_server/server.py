import sys
import logging
from mcp.server.fastmcp import FastMCP
from mcp_server import tools

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

mcp = FastMCP("openprinttag-architecture")


@mcp.tool()
def get_tools_guide() -> dict:
    """Returns descriptions of all tools and recommended call sequences. Call this first."""
    return tools.get_tools_guide()


@mcp.tool()
def get_overview() -> dict:
    """All entities and enums with short descriptions and field counts."""
    return tools.get_overview()


@mcp.tool()
def get_entity(name: str) -> dict:
    """Full field-level schema for one entity.

    Args:
        name: Entity name, e.g. 'Material', 'Brand', 'MaterialPackage'
    """
    return tools.get_entity(name)


@mcp.tool()
def get_enum(name: str) -> dict:
    """All non-deprecated values for one enum.

    Args:
        name: Enum stem, e.g. 'material_types', 'material_tags'
    """
    return tools.get_enum(name)


@mcp.tool()
def get_relationships(entity: str) -> dict:
    """Inheritance and field-level references for one entity.

    Args:
        entity: Entity name, e.g. 'Material'
    """
    return tools.get_relationships(entity)


@mcp.tool()
def get_examples(entity: str) -> dict:
    """Constructs a valid example object from the YAML example values.

    Args:
        entity: Entity name, e.g. 'Material'
    """
    return tools.get_examples(entity)


@mcp.tool()
def validate_data(entity: str, data: dict) -> dict:
    """Validates a JSON object against the architecture schema.
    Checks required fields, max_length, and enum membership.

    Args:
        entity: Entity name, e.g. 'Material'
        data: JSON object to validate
    """
    return tools.validate_data(entity, data)


@mcp.tool()
def find_discrepancies(schema: dict) -> dict:
    """Compares a downstream schema against the architecture.
    Reports missing fields, type mismatches, and extra fields.

    Args:
        schema: {"entity": str, "fields": [{"name": str, "type": str, "required"?: bool}]}
    """
    return tools.find_discrepancies(schema)


@mcp.tool()
def get_full_context() -> str:
    """Full architecture as Markdown (same content as llms-full.txt).
    For CI pipelines and headless agents.
    """
    return tools.get_full_context()


@mcp.tool()
def search(query: str) -> list:
    """Full-text search across entity names, field names, descriptions, and enum values.

    Args:
        query: Search term, e.g. 'uuid', 'color', 'required'
    """
    return tools.search(query)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
