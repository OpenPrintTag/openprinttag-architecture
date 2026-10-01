from material_schema_generator import MaterialSchemaGenerator
from schema_generator import SchemaGenerator

g = SchemaGenerator(
    out_dir="opt_db_schema",
)

slug_extension = {
    "properties": {
        "slug": {
            "type": "string",
            "description": "Identifier within the material database directory structure. Has to correspond with entity yaml the filename.",
        },
    },
}

mg = MaterialSchemaGenerator(g, root_entity_extension=slug_extension)

g.add_source_file("brands.yaml")
g.add_source_file("materials.yaml")
g.add_source_file("packaging.yaml")
g.add_source_file("auxiliary_media.yaml")


def object_ref_or_link(entity_name: str, object_schema_filename: str):
    return {
        "title": entity_name,
        "oneOf": [
            g.object_ref(None, object_schema_filename),
            g.object_ref(None, "slug_reference"),
            g.object_ref(None, "uuid_reference"),
        ],
    }


g.export_file(
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

g.export_file(
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

g.add_known_type_schema(object_ref_or_link("Brand", "brand"))
g.add_known_type_schema(object_ref_or_link("Material", "material"))
g.add_known_type_schema(object_ref_or_link("MaterialContainer", "material_container"))
g.add_known_type_schema(object_ref_or_link("SLAMaterialContainerConnector", "sla_material_container_connector"))
g.add_known_type_schema(g.entity("Container"))

mg.add_small_country()
g.export_file("country", g.entity("Country"))

g.add_known_type_schema(g.enum("BrandLinkPatternType", "brand_link_pattern_types.yaml", key_field="name"))
g.add_known_type_schema(g.entity("BrandLinkPattern"))

g.add_known_type_schema(g.enum("MaterialPhotoType", "material_photo_types.yaml", key_field="name"))
g.add_known_type_schema(g.entity("MaterialPhoto"))

mg.export_brand()
mg.export_material()
mg.export_package()

g.export_file("sla_material_container_connector", g.entity("SLAMaterialContainerConnector"))

g.export_file("wash_medium", g.recursive_merge(g.entity("WashMedium"), slug_extension))
g.export_file("sla_wash_medium_container", g.entity("SLAWashMediumContainer", include_inherits=True))
