import tables
from generate_common import ProjectTag, env, generate

env.globals["country_columns"] = [
    tables.Column(field="code", title="Code"),
    tables.Column(field="name", title="Name"),
    tables.Column(field="flag", title="Flag"),
]

generate(
    files=[
        "_navbar",
        "README",
        "brands",
        "materials",
        "material_tags",
        "material_types",
        "material_certifications",
        "packaging",
        "uuid",
    ],
    project_tag_list={
        "in_opt_db": ProjectTag("DB", "DB", "In the database"),
        "in_opt": ProjectTag("OPT", "OPT", "In OpenPrintTag"),
    },
)
