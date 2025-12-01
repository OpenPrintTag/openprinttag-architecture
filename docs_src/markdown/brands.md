# Brands

## Entity diagram
{{ plantuml("brands.plantuml") }}

{{ class_documentation("brands.yaml", "Brand") }}

{{ class_documentation("brands.yaml", "BrandLinkPattern") }}

{{ class_documentation("brands.yaml", "BrandLinkPatternType") }}
{{ enum_table("brand_link_pattern_types.yaml") }}

### Examples of patterns and matching
* `https://prusament.com/spool/?spoolId=123858541`
	* `brand`: "Prusament"
	* `object_type`: `MaterialPackageInstance`
	* `MaterialPackageInstance::uid`: `123858541`

* `https://www.prusa3d.com/cs/produkt/prusament-petg-jet-black-1kg/`
	* `brand`: "Prusament"
	* `object_type`: `MaterialPackage`
	* (Specific material type not decipherable from the link)

{{ class_documentation("brands.yaml", "Country") }}
