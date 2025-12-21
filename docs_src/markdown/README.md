# OpenPrintTag Architecture
OpenPrintTag architecture is a high-level, abstract model of a variety of entities relevant to the OpenPrintTag initiative. It defines a common ground and ontology for the tag data format and OpenPrintTag database.

Not all parts of the architecture are used by both projects. For example, the database stores data up to the `MaterialPackage` level, disregarding `MaterialPackageInstance` and lower. And the tag itself does not contain some of the fields from the database due to memory constraints and to keep the data format simple. This is indicated by the `<<DB>>` and `<OPT>` tags in the entities.

The architecture also defines shared enums, and it is used to automatically generate database schemas.

### Quick links
* [OpenPrintTag landing page](https://openprinttag.org)
* [OpenPrintTag NFC tag specification](https://specs.openprinttag.org)

### General notes
* `list(Type)` denotes a list of `Type` - a relation where **order does matter**.
* `set(Type)` denotes a set of `Type` - a relation where order **does not matter**.
* Use `min` and `max` instead of `minimum` and `maximum` in field names.
