#!/bin/bash

set -e

SCRIPT=$(realpath "$0")
BASE_PATH=$(dirname "$SCRIPT")

cd "$BASE_PATH/schema"
rm -rf "generated"
mkdir "generated"

python3 "$BASE_PATH/schema/generate_db_schema.py"
