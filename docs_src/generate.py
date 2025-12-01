from generate_common import generate, ProjectTag

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
