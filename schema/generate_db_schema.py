from generate_schema_common import (
    object_ref_schema,
    array_schema,
    read_yaml,
    enum_schema,
    entity_yaml,
    generate_schema_file,
    register_type_schema,
    entity_schema,
    setup,
    type_schema,
)

setup("opt_db_schema", "required_in_opt_db", "in_opt_db")

material_class_schema = {
    "type": "string",
    "enum": ["FFF", "SLA"],
}

materials_yaml = read_yaml("materials")

register_type_schema("Country", {"type": "string", "minLength": 2, "maxLength": 2})
register_type_schema("list(Country)", array_schema(type_schema("Country", None)))

register_type_schema("Brand", object_ref_schema("brand"))
register_type_schema("Material", object_ref_schema("material"))
register_type_schema("MaterialClass", material_class_schema)
register_type_schema("MaterialType", enum_schema(read_yaml("material_types"), name_item="abbreviation"))
register_type_schema("MaterialContainer", object_ref_schema("material_container"))
register_type_schema(
    "SLAMaterialContainerConnector",
    object_ref_schema("sla_material_container_connector"),
)
register_type_schema("PaletteColor", object_ref_schema("palette_color"))

register_type_schema("set(MaterialTag)", array_schema(enum_schema(read_yaml("material_tags"))))
register_type_schema("MaterialPhotoType", enum_schema(read_yaml("material_photo_types")))
register_type_schema(
    "set(MaterialPhoto)",
    array_schema(entity_schema(entity_yaml(materials_yaml, "MaterialPhoto"))),
)
register_type_schema(
    "set(MaterialCertification)",
    array_schema(entity_schema(entity_yaml(materials_yaml, "MaterialCertification"))),
)
register_type_schema("MaterialProperties", object_ref_schema("material_properties"))

register_type_schema("set(PaletteColor)", array_schema(type_schema("PaletteColor", None)))


register_type_schema("MaterialColor", entity_schema(entity_yaml(materials_yaml, "MaterialColor")))
register_type_schema("set(MaterialColor)", array_schema(type_schema("MaterialColor", None)))

generate_schema_file("material", entity_schema(entity_yaml(materials_yaml, "Material")))
generate_schema_file("material_type", entity_schema(entity_yaml(materials_yaml, "MaterialType")))

generate_schema_file(
    "fff_material_properties",
    entity_schema(entity_yaml(materials_yaml, "FFFMaterialProperties"), include_inherits=False),
)
generate_schema_file(
    "sla_material_properties",
    entity_schema(entity_yaml(materials_yaml, "SLAMaterialProperties"), include_inherits=False),
)

generate_schema_file(
    "material_properties",
    entity_schema(entity_yaml(materials_yaml, "MaterialProperties")),
    {
        "anyOf": [
            {"$ref": "fff_material_properties.schema.json"},
            {"$ref": "sla_material_properties.schema.json"},
        ],
    },
)

brands_yaml = read_yaml("brands")

register_type_schema("BrandLinkPatternType", enum_schema(read_yaml("brand_link_pattern_types")))
register_type_schema(
    "set(BrandLinkPattern)",
    array_schema(entity_schema(entity_yaml(brands_yaml, "BrandLinkPattern"))),
)

generate_schema_file("brand", entity_schema(entity_yaml(brands_yaml, "Brand")))

packaging_yaml = read_yaml("packaging")

generate_schema_file(
    "material_package",
    entity_schema(entity_yaml(packaging_yaml, "MaterialPackage")),
    {
        "properties": {
            "class": material_class_schema,
        },
        "oneOf": [
            {
                "propreties": {"class": {"const": "FFF"}},
                "$ref": "fff_material_package.schema.json",
            },
            {
                "propreties": {"class": {"const": "SLA"}},
                "$ref": "sla_material_package.schema.json",
            },
        ],
    },
)
generate_schema_file(
    "fff_material_package",
    entity_schema(entity_yaml(packaging_yaml, "FFFMaterialPackage"), include_inherits=False),
)
generate_schema_file(
    "sla_material_package",
    entity_schema(entity_yaml(packaging_yaml, "SLAMaterialPackage"), include_inherits=False),
)

generate_schema_file(
    "material_container",
    entity_schema(entity_yaml(packaging_yaml, "MaterialContainer")),
    {
        "properties": {
            "class": material_class_schema,
        },
        "oneOf": [
            {
                "propreties": {"class": {"const": "FFF"}},
                "$ref": "fff_material_container.schema.json",
            },
            {
                "propreties": {"class": {"const": "SLA"}},
                "$ref": "sla_material_container.schema.json",
            },
        ],
    },
)
generate_schema_file(
    "fff_material_container",
    entity_schema(entity_yaml(packaging_yaml, "FFFMaterialContainer"), include_inherits=False),
)
generate_schema_file(
    "sla_material_container",
    entity_schema(entity_yaml(packaging_yaml, "SLAMaterialContainer"), include_inherits=False),
)
generate_schema_file(
    "sla_material_container_connector",
    entity_schema(entity_yaml(packaging_yaml, "SLAMaterialContainerConnector")),
)

generate_schema_file("material_color", entity_schema(entity_yaml(materials_yaml, "MaterialColor")))
