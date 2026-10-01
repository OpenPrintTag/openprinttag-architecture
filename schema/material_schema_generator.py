import yaml
from schema_generator import Schema, SchemaGenerator, YamlData, data_dir

material_classes_yaml = yaml.safe_load((data_dir / "material_classes.yaml").read_text())


class MaterialSchemaGenerator:
    _g: SchemaGenerator
    _root_entity_extension: Schema

    def __init__(self, g: SchemaGenerator, *, root_entity_extension: Schema | None = None):
        self._g = g
        self._root_entity_extension = root_entity_extension or {}

    def _export_root_entity(self, basename: str, schema: Schema):
        self._g.export_file(basename, self._g.recursive_merge(schema, self._root_entity_extension))

    def _material_class_extension(self, then_lambda):
        return [
            {
                "if": {
                    "properties": {
                        "class": {"const": class_yaml["name"]},
                    },
                    "required": ["class"],
                },
                "then": then_lambda(class_yaml),
            }
            for class_yaml in material_classes_yaml
        ]

    def _material_class_extension_entity(self, class_yaml: YamlData, key: str):
        if t := class_yaml.get(key):
            return self._g.entity(t, include_inherits=False)
        else:
            return {}

    def add_small_country(self):
        self._g.add_known_type_schema(
            {
                "title": "Country",
                "description": "Two-letter country code, according to [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)",
                "type": "string",
                "minLength": 2,
                "maxLength": 2,
            },
        )

    def export_brand(self):
        self._g.add_source_file("brands.yaml")
        self._export_root_entity("brand", self._g.entity("Brand"))

    def export_material(self):
        self._g.add_source_file("materials.yaml")

        self._g.export_file("material_class", self._g.enum("MaterialClass", "material_classes.yaml", key_field="name"))
        self._g.add_known_type_schema(self._g.object_ref("MaterialClass", "material_class"))

        self._g.export_file("material_color", self._g.entity("MaterialColor"))
        self._g.add_known_type_schema(self._g.object_ref("MaterialColor", "material_color"))

        material_properties_schema = self._g.entity("MaterialProperties")
        material_properties_refs = {}

        for class_yaml in material_classes_yaml:
            if t := class_yaml.get("properties"):
                basename = f"{class_yaml['name'].lower()}_material_properties"
                self._g.export_file(
                    basename,
                    self._g.entity(
                        t,
                        include_inherits=True,
                        type_schemas={
                            # Needs to be a direct schema, not a $ref, otherwise the validator would enforce "unevaluatedProperties: false" on the parent class alone
                            "MaterialProperties": material_properties_schema,
                        },
                    ),
                )
                ref = self._g.object_ref(t, basename)
                self._g.add_known_type_schema(ref)
                material_properties_refs[class_yaml["name"]] = ref
            else:
                material_properties_refs[class_yaml["name"]] = material_properties_schema

        self._g.export_file("fff_material_type", self._g.entity("FFFMaterialType"))
        self._g.add_known_type_schema(self._g.enum("FFFMaterialType", "fff_material_types.yaml", key_field="abbreviation"))

        self._g.export_file("material_tag", self._g.enum("MaterialTag", "material_tags.yaml", key_field="name"))
        self._g.add_known_type_schema(self._g.object_ref("MaterialTag", "material_tag"))

        self._g.export_file("material_certification", self._g.enum("MaterialCertification", "material_certifications.yaml", key_field="name"))
        self._g.add_known_type_schema(self._g.object_ref("MaterialCertification", "material_certification"))

        self._export_root_entity(
            "material",
            self._g.recursive_merge(
                self._g.entity(
                    "Material",
                    type_schemas={
                        # Enforced per-class by the allOf below
                        "MaterialProperties": {},
                    },
                ),
                {
                    "allOf": self._material_class_extension(
                        lambda class_yaml: self._g.recursive_merge(
                            self._material_class_extension_entity(class_yaml, "type"),
                            {
                                "properties": {
                                    "properties": material_properties_refs[class_yaml["name"]],
                                },
                            },
                        ),
                    ),
                },
            ),
        )

    def export_package(self):
        self._g.add_source_file("packaging.yaml")

        self._export_root_entity(
            "material_container",
            self._g.recursive_merge(
                self._g.entity("MaterialContainer", include_inherits=True),
                {
                    "allOf": self._material_class_extension(lambda class_yaml: self._material_class_extension_entity(class_yaml, "container")),
                },
            ),
        )

        self._export_root_entity(
            "material_package",
            self._g.recursive_merge(
                self._g.entity("MaterialPackage"),
                {
                    "allOf": self._material_class_extension(lambda class_yaml: self._material_class_extension_entity(class_yaml, "package")),
                },
            ),
        )

    def export_package_instance_dynamic(self):
        self._g.add_source_file("packaging.yaml")

        self._g.export_file(
            "material_package_dynamic_data",
            self._g.recursive_merge(
                self._g.entity("MaterialPackageDynamicData", include_inherits=True),
                {
                    "allOf": self._material_class_extension(lambda class_yaml: self._material_class_extension_entity(class_yaml, "package_instance_dynamic_data")),
                },
            ),
        )

    def export_package_instance(self):
        self._g.add_source_file("packaging.yaml")

        self._export_root_entity(
            "material_package_instance",
            self._g.recursive_merge(
                self._g.entity("MaterialPackageInstance", include_inherits=True),
                {
                    "allOf": self._material_class_extension(lambda class_yaml: self._material_class_extension_entity(class_yaml, "package_instance")),
                },
            ),
        )
