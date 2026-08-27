import shutil
import os
import jinja2
import jinja2.ext
import subprocess
import urllib.request
import yaml
import typing
import pathlib
import io
import sys

import vars
import tables

# Re-create output directory
shutil.rmtree(vars.out_dir, ignore_errors=True)
os.mkdir(vars.out_dir)

# Build dir
os.makedirs(vars.build_dir, exist_ok=True)


def download_dependency(file, url):
    if not os.path.isfile(file):
        urllib.request.urlretrieve(url, file)

    return file


plantuml_jar = download_dependency(
    f"{vars.build_dir}/plantuml-mit-1.2025.1.jar",
    "https://github.com/plantuml/plantuml/releases/download/v1.2025.1/plantuml-mit-1.2025.1.jar",
)

# Copy the docsify index.html
shutil.copyfile(f"{vars.dir}/index.html", f"{vars.out_dir}/index.html")

# Set up jinja
env = jinja2.Environment(loader=jinja2.FileSystemLoader(vars.dir))
jinja_args = {}


# Two-pass generation: a first, throwaway "dry run" pass renders every page so that every entity
# documented via class_documentation() gets tagged with the page it lives on (see "documentation_page"
# below); a second, real pass then has that mapping available to resolve cross-page inheritance links,
# regardless of which order pages happen to be generated in.
_dry_run = False
current_page = None

# PlantUML support
current_plantuml = None


def gen_plantuml(source_file):
    global current_plantuml

    # Diagrams don't affect the class_documentation()-derived page mapping, and rendering them
    # (which shells out to PlantUML/Java) is expensive, so skip them entirely during the dry run.
    if _dry_run:
        return ""

    rendered_uml_file = f"{vars.out_dir}/{source_file}"

    with open(rendered_uml_file, "w") as f:
        current_plantuml = source_file
        f.write(env.get_template(f"plantuml/{source_file}").render(jinja_args))
        current_plantuml = None

    rendered_img_file = os.path.splitext(source_file)[0] + ".svg"
    args = ["java", "-jar", plantuml_jar, "-o", vars.out_dir, "-tsvg", rendered_uml_file]
    subprocess.run(args)

    result = f'<img src="{rendered_img_file}">'
    result += f"*The graph was automatically generated from [`{source_file}`]({vars.repo}/blob/main/docs_src/plantuml/{source_file})*\n\n"

    return result


env.globals["plantuml"] = gen_plantuml


class ProjectTag(typing.NamedTuple):
    stereotype: str
    shorthand: str
    description: str


_project_tag_list = {}
entity_yamls = dict()
enum_yamls = dict()

# Scan the data directory and load up all the yamls
for file in pathlib.Path(vars.data_dir).glob("*.yaml"):
    data = yaml.safe_load(open(os.path.join(vars.data_dir, file), "r"))
    key = str(file)
    if isinstance(data, dict):
        entity_yamls[key] = data
        for item in data["objects"]:
            item["source_yaml_file"] = file.name

    elif isinstance(data, list):
        enum_yamls[key] = {"items": data}

    else:
        assert False


def get_entity_yaml(yaml_file, class_name):
    yaml_file = f"{vars.data_dir}/{yaml_file.removesuffix('.yaml')}.yaml"
    item = next((item for item in entity_yamls[yaml_file]["objects"] if item["name"] == class_name))

    return item


def find_entity_yaml(class_name):
    matches = [item for data in entity_yamls.values() for item in data["objects"] if item["name"] == class_name]

    assert len(matches) > 0, f"Could not find entity {class_name} in any data file"
    assert len(matches) == 1, f"Entity {class_name} is defined in more than one data file, class names must be globally unique"

    return matches[0]


def _slugify(class_name):
    return class_name.lower()


def _inheritance_chain_links(item):
    links = []
    current = item

    while (parent_name := current.get("inherits", None)) is not None:
        current = find_entity_yaml(parent_name)
        page = current.get("documentation_page")
        assert page is not None, f"Class {parent_name} has no documented page (missing class_documentation call?)"

        links.append(f"[{parent_name}](/{page}?id={_slugify(parent_name)})")

    return links


def gen_plantuml_entity_ref(yaml_file, class_name):
    item = get_entity_yaml(yaml_file, class_name)

    stereotypes = "".join(f"<<{_project_tag_list[key].stereotype}>>" for key in _project_tag_list if item.get(key, False))
    result = f"entity {class_name} {stereotypes}\n"
    return result


env.globals["plantuml_entity_ref"] = gen_plantuml_entity_ref


def gen_plantuml_entity(class_name, custom_inheritance=None):
    yaml_file = os.path.splitext(os.path.basename(current_plantuml))[0]
    item = get_entity_yaml(yaml_file, class_name)

    assert "plantuml_entity_generated" not in data, f"Double plantuml_entity call for {class_name}"
    item["plantuml_entity_generated"] = True

    result = gen_plantuml_entity_ref(yaml_file, class_name)
    result += "{\n"

    for field in item.get("fields", []):
        if field.get("primary_key", False):
            result += "*"

        # If the name doesn't contain "(", it is a field and not a method
        # Enforce the fieldness in this case, because the type might contain `(` and PlantUML would be misinterpreting it
        if "(" not in field["name"]:
            result += "{field} "

        result += field["name"]

        if field.get("type", None) is not None:
            result += f": {field['type']}"

        result += "".join(f" ${key}" for key in _project_tag_list if field.get(key, False))
        result += "\n"

    result += "}\n"

    # True -> custom arrow
    # String -> provided arrow
    # None -> default arrow
    if custom_inheritance is not True and (parent := item.get("inherits", None)):
        arrow = custom_inheritance if custom_inheritance is not None else "-u-|>"
        result += f"{class_name} {arrow} {parent}"

    return result


env.globals["plantuml_entity"] = gen_plantuml_entity


def gen_projects_common():
    result = "legend\n"

    for key, data in _project_tag_list.items():
        result += f"<<{data.stereotype}>> ${key} {data.description}\n"

    result += "end legend\n"

    return result


env.globals["projects_common"] = gen_projects_common

# Other documentation support

class_columns = [
    tables.Column(field="name", title="Name", transform=lambda x: f"`{x}`"),
    tables.Column(field="type", title="Type", transform=lambda x: f"`{x}`"),
    tables.Column(field="unit", title="Unit"),
    tables.Column(field="example", title="Example"),
    tables.Column(field="description", title="Description"),
]


def gen_class_documentation(class_name):
    item = find_entity_yaml(class_name)

    # The dry run only exists to find out which page each class ends up documented on
    # (see the module-level comment above current_page), so nothing else is needed here.
    if _dry_run:
        item["documentation_page"] = current_page
        return ""

    assert "documentation_generated" not in item, f"Double class_documentation call for {class_name}"
    item["documentation_generated"] = True

    result = f"# {class_name}\n"

    chain = _inheritance_chain_links(item)
    if len(chain):
        result += f"**Inherits from:** {' → '.join(chain)}\n\n"

    projects = ", ".join(data.stereotype for key, data in _project_tag_list.items() if item.get(key, False))
    if len(projects):
        result += f"> Used in: {projects}\n\n"

    if item.get("description", None) is not None:
        result += tables.default_transform(item["description"])
        result += "\n\n"

    yaml_file = item["source_yaml_file"]
    result += tables.generate_table(item["fields"], class_columns)
    result += f"*The documentation was automatically generated from [`{yaml_file}`]({vars.repo}/blob/main/data/{yaml_file})*\n\n"

    return result


env.globals["class_documentation"] = gen_class_documentation

enum_columns = [
    tables.Column(field="key", title="ID"),
    tables.Column(field="name", title="Name", transform=lambda x: f"`{x}`"),
    tables.Column(field="description", title="Description"),
]


def gen_enum_table(yaml_file, columns=enum_columns):
    data = enum_yamls[os.path.join(vars.data_dir, yaml_file)]

    if _dry_run:
        return ""

    assert "table_generated" not in data
    data["table_generated"] = True

    result = tables.generate_table(data["items"], columns)
    result += f"*The table was automatically generated from [`{yaml_file}`]({vars.repo}/blob/main/data/{yaml_file})*\n\n"
    return result


env.globals["enum_table"] = gen_enum_table


def gen_material_tag_table():
    r = io.StringIO("")
    r.write("<table>")
    r.write("<tr><th>ID</th><th>Name</th><th>Display name</th><th>Info</th>")

    tags = enum_yamls[os.path.join(vars.data_dir, "material_tags.yaml")]
    tags["table_generated"] = True
    tags = tags["items"]

    yaml_file = "material_tag_categories.yaml"
    categories = enum_yamls[os.path.join(vars.data_dir, yaml_file)]["items"]
    categories_keys = {c["name"] for c in categories}

    # Check that all tags have a matching category
    for tag in tags:
        if tag.get("deprecated", False):
            continue

        assert tag["category"] in categories_keys, f"Tag {tag['name']} category {tag['category']} is not in material_tag_categories.yaml"

    for cat in categories:
        r.write(f"<tr><th colspan='4' align='left'>{cat['emoji']} {cat['display_name']}</th></tr>")

        for tag in tags:
            if tag.get("deprecated", False):
                continue

            if tag["category"] != cat["name"]:
                continue

            r.write("<tr>")
            r.write(f"<td>{tag['key']}</td>")
            r.write(f"<td><code>{tag['name']}</code></td>")
            r.write(f"<td>{tag['display_name']}</td>")

            r.write("<td>")

            desc_lines = []

            desc = tag.get("description", [])
            if isinstance(desc, list):
                desc_lines += desc
            elif len(desc.strip()) > 0:
                desc_lines.append(desc)

            implies = tag.get("implies", [])
            if len(implies) > 0:
                desc_lines.append("Implies " + ", ".join(map(lambda i: f"<code>{i}</code>", implies)))

            hints = tag.get("hints", [])
            if len(hints) > 0:
                desc_lines.append("Hints " + ", ".join(map(lambda i: f"<code>{i}</code>", hints)))

            r.write("<br>".join(desc_lines))
            r.write("</td></tr>")

    r.write("</table>\n\n")
    r.write(f"*The documentation was automatically generated from [`{yaml_file}`]({vars.repo}/blob/main/data/{yaml_file})*\n\n")

    return r.getvalue()


env.globals["material_tag_table"] = gen_material_tag_table

env.globals["fff_material_type_columns"] = [
    tables.Column(field="key", title="ID"),
    tables.Column(field="abbreviation", title="Abbr.", transform=lambda x: f"`{x}`"),
    tables.Column(field="name", title="Name"),
    tables.Column(field="description", title="Description"),
]

env.globals["material_tag_category_columns"] = [
    tables.Column(field="name", title="Name", transform=lambda x: f"`{x}`"),
    tables.Column(field="emoji", title="Emoji"),
    tables.Column(field="display_name", title="Display name"),
]

env.globals["material_certification_columns"] = [
    tables.Column(field="key", title="ID"),
    tables.Column(field="name", title="ID (str)", transform=lambda x: f"`{x}`"),
    tables.Column(field="display_name", title="Name"),
    tables.Column(field="description", title="Description"),
]

# Examples support


class PythonCodeExtension(jinja2.ext.Extension):
    tags = {"python"}

    def parse(self, parser):
        next(parser.stream)
        body = parser.parse_statements(["name:endpython"], drop_needle=True)
        return jinja2.nodes.CallBlock(self.call_method("_render"), [], [], body)

    def _render(self, caller):
        code = caller()
        result = f"> ```python\n> {code.strip().replace('\n', '\n> ')}\n> ```\n"

        out_buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = out_buf
        exec(code, globals().copy())
        sys.stdout = old_stdout

        result += f"```\n{out_buf.getvalue()}```"

        return result


env.add_extension(PythonCodeExtension)

# Other variables
env.globals["repo"] = vars.repo


# Generate documentation files
def gen_doc_file(source_file, dry_run):
    global current_page, _dry_run
    current_page = source_file
    _dry_run = dry_run
    rendered = env.get_template(f"markdown/{source_file}.md").render(jinja_args)
    current_page = None
    _dry_run = False

    if not dry_run:
        with open(f"{vars.out_dir}/{source_file}.md", "w") as f:
            f.write(rendered)


def generate(files: list[str], project_tag_list: dict[str, ProjectTag]):
    global _project_tag_list
    _project_tag_list = project_tag_list

    # Uses project_tag_list
    env.globals["plantuml_common"] = env.get_template("plantuml/_common.plantuml").render(jinja_args)

    # First, throwaway pass: find out which page every class ends up documented on (see gen_class_documentation).
    for file in files:
        gen_doc_file(file, dry_run=True)

    # Second, real pass: render the actual output, now with inheritance links resolvable.
    for file in files:
        gen_doc_file(file, dry_run=False)

    for enum, data in enum_yamls.items():
        assert data.get("table_generated", False), f"Enum {os.path.basename(enum)} does not have any corresponding enum_table call"

    for data in entity_yamls.values():
        for obj in data["objects"]:
            assert obj.get("plantuml_entity_generated", False), f"Entity {obj['name']} does not have any corresponding plantuml_entity call"
            assert obj.get("documentation_generated", False), f"Entity {obj['name']} does not have any corresponding class_documentation call"
