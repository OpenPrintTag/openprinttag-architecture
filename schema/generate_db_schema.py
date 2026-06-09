from generate_schema_common import (
    array_schema,
    entity_schema,
    entity_yaml,
    enum_schema,
    generate_schema_file,
    object_ref_schema,
    read_yaml,
    register_type_schema,
    setup,
    type_schema,
)

setup("opt_db_schema", "required_in_opt_db", "in_opt_db")


def object_ref_or_link_schema(object_schema_file: str):
    return {
        "oneOf": [
            object_ref_schema(object_schema_file),
            object_ref_schema("slug_reference"),
            object_ref_schema("uuid_reference"),
        ]
    }


def add_slug_property(schema: dict):
    schema["properties"]["slug"] = {
        "type": "string",
        "description": "Identifier within the material database directory structure. Has to correspond with entity yaml the filename.",
    }
    return schema


material_class_schema = {
    "type": "string",
    "enum": ["FFF", "SLA"],
}

materials_yaml = read_yaml("materials")

generate_schema_file(
    "uuid_reference",
    {
        "type": "object",
        "properties": {
            "uuid": {
                "type": "string",
                "format": "uuid",
                "description": "Reference to the entity",
            },
        },
        "required": ["uuid"],
        "unevaluatedProperties": False,
    },
)
generate_schema_file(
    "slug_reference",
    {
        "type": "object",
        "properties": {
            "slug": {
                "type": "string",
                "description": "Location of the entity within the openprinttag-database directory structure",
            },
        },
        "required": ["slug"],
        "unevaluatedProperties": False,
    },
)

register_type_schema("Country", {"type": "string", "minLength": 2, "maxLength": 2})
register_type_schema("list(Country)", array_schema(type_schema("Country", None)))

register_type_schema("Brand", object_ref_or_link_schema("brand"))
register_type_schema("Material", object_ref_or_link_schema("material"))
register_type_schema("MaterialClass", material_class_schema)
register_type_schema("MaterialType", enum_schema(read_yaml("material_types"), name_item="abbreviation"))
register_type_schema("MaterialContainer", object_ref_or_link_schema("material_container"))
register_type_schema(
    "SLAMaterialContainerConnector",
    object_ref_or_link_schema("sla_material_container_connector"),
)

register_type_schema("set(MaterialTag)", array_schema(enum_schema(read_yaml("material_tags"))))
register_type_schema("MaterialPhotoType", enum_schema(read_yaml("material_photo_types")))
register_type_schema(
    "set(MaterialPhoto)",
    array_schema(entity_schema(entity_yaml(materials_yaml, "MaterialPhoto"))),
)
register_type_schema(
    "set(MaterialCertification)",
    array_schema(enum_schema(read_yaml("material_certifications"))),
)
register_type_schema("MaterialProperties", object_ref_schema("material_properties"))

register_type_schema("MaterialColor", object_ref_schema("material_color"))
register_type_schema("set(MaterialColor)", array_schema(type_schema("MaterialColor", None)))

generate_schema_file(
    "material",
    add_slug_property(entity_schema(entity_yaml(materials_yaml, "Material"))),
    {
        "allOf": [
            {
                "if": {"properties": {"class": {"const": "FFF"}}},
                "then": {"properties": {"properties": {"$ref": "fff_material_properties.schema.json"}}},
            },
            {
                "if": {"properties": {"class": {"const": "SLA"}}},
                "then": {"properties": {"properties": {"$ref": "sla_material_properties.schema.json"}}},
            },
        ],
    },
)
generate_schema_file("material_type", entity_schema(entity_yaml(materials_yaml, "MaterialType")))

generate_schema_file(
    "fff_material_properties",
    entity_schema(entity_yaml(materials_yaml, "FFFMaterialProperties"), include_inherits=True),
)
generate_schema_file(
    "sla_material_properties",
    entity_schema(entity_yaml(materials_yaml, "SLAMaterialProperties"), include_inherits=True),
)


generate_schema_file("material_properties", entity_schema(entity_yaml(materials_yaml, "MaterialProperties"), include_inherits=False))

brands_yaml = read_yaml("brands")

register_type_schema("BrandLinkPatternType", enum_schema(read_yaml("brand_link_pattern_types")))
register_type_schema(
    "set(BrandLinkPattern)",
    array_schema(entity_schema(entity_yaml(brands_yaml, "BrandLinkPattern"))),
)

generate_schema_file("brand", add_slug_property(entity_schema(entity_yaml(brands_yaml, "Brand"))))

packaging_yaml = read_yaml("packaging")

generate_schema_file(
    "material_package",
    add_slug_property(entity_schema(entity_yaml(packaging_yaml, "MaterialPackage"))),
    {
        "oneOf": [
            {
                "properties": {"class": {"const": "FFF"}},
                "$ref": "fff_material_package.schema.json",
            },
            {
                "properties": {"class": {"const": "SLA"}},
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
    add_slug_property(entity_schema(entity_yaml(packaging_yaml, "MaterialContainer"))),
    {
        "properties": {
            "class": material_class_schema,
        },
        "oneOf": [
            {
                "properties": {"class": {"const": "FFF"}},
                "$ref": "fff_material_container.schema.json",
            },
            {
                "properties": {"class": {"const": "SLA"}},
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

generate_schema_file("country", entity_schema(entity_yaml(brands_yaml, "Country")))
