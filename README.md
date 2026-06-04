# OpenPrintTag Architecture

This repository contains machine-readable (YAML) files that define entity structure/ontology that is shared between the OpenPrintTag NFC Data Format and OpenPrintTag Database.

These ontology files are then used:
1. To generate [the architecture documentation website](https://arch.openprinttag.org) (see `docs_src/`)
1. To generate JSON/YAML schemas for the Database itself (see `schema/`)

### Running the documentation website locally
You can run the documentation website locally using these commands:
```
pip3 install -r requirements.txt
sh generate_docs.sh
cd docs
python3 -m http.server
``˙
Then open your browser on 127.0.0.1:8000

### For LLMs and AI agents

The architecture is available as LLM-friendly context files, auto-generated from the same YAML source:

| Resource | URL | Use |
|----------|-----|-----|
| `llms.txt` | `https://arch.openprinttag.org/llms.txt` | Navigation index, auto-discovered by Claude Code, Cursor, Copilot, Windsurf |
| `llms-full.txt` | `https://arch.openprinttag.org/llms-full.txt` | Full entity + enum context, load into any LLM |
| JSON Schemas | `https://arch.openprinttag.org/schema/` | Per-entity JSON Schema files for programmatic validation |

#### MCP server (for Claude Code and MCP-compatible tools)

The repo includes a local MCP server that reads the YAML files directly and exposes 10 tools
(`get_overview`, `get_entity`, `get_enum`, `get_relationships`, `get_examples`,
`validate_data`, `find_discrepancies`, `get_full_context`, `search`, `get_tools_guide`).

**Setup** — add to `.claude/settings.json` in a downstream repo (or `~/.claude/settings.json` globally):

```json
{
  "mcpServers": {
    "openprinttag-arch": {
      "command": "python3",
      "args": ["/absolute/path/to/openprinttag-architecture/mcp_server/server.py"]
    }
  }
}
```

Requires a local clone of this repo and `pip install mcp>=1.2.0 pyyaml`.

#### Adding context to a downstream repo's CLAUDE.md

```markdown
## Architecture reference
Shared domain model: https://arch.openprinttag.org/llms-full.txt
JSON Schemas: https://arch.openprinttag.org/schema/{EntityName}.schema.json
```
