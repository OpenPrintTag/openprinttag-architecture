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
