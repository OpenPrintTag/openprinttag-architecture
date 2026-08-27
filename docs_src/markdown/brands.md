# Brands

## Entity diagram
{{ plantuml("brands.plantuml") }}

{{ class_documentation("Brand") }}

{{ class_documentation("BrandLinkPattern") }}

{{ class_documentation("BrandLinkPatternType") }}
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

{{ class_documentation("Country") }}

<details>
<summary><b>Full country list</b></summary>

{{ enum_table("countries.yaml", country_columns) }}
