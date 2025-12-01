# UUID
The architecture employs [UUIDs](https://en.wikipedia.org/wiki/Universally_unique_identifier) as primary keys for some of the objects. In the ideal world, all of the UUIDs would be provided by the manufacturers, but it is safe to expect that the adoption of UUIDs would be very low.

For that, we define a way how to derive UUIDs from other known parameters in a standardized manner if the UUID is not specified by the manufacturer.

UUIDs are be derived from the brand-specific IDs using UUIDv5 with the `SHA1` hash, as specified in [RFC 4122, section 4.3](https://datatracker.ietf.org/doc/html/rfc4122#section-4.3), according to the following table.
* UUIDs are hashed in the binary form.
* Strings are encoded as UTF-8.
* Numbers are encoded as decimal strings.
* `+` represents binary concatenation.
* NFC tag UID is represented as a bytestream with the MSB being the first byte in the bytestream.
   * **Important:** Various apps/readers report these UIDs in various byte orders, and sometimes as hex strings instead of bytestreams. For NFCV, the UID MUST be a 8 bytes long bytestream with `0xE0` as the **first** byte (SLIX2 then follows with `0x04, 0x01`).

| UID | Derviation formula | Namespace (`N`) |
| --- | --- | --- |
| `Brand::uuid` | `N + Brand::name` | `5269dfb7-1559-440a-85be-aba5f3eff2d2` |
| `Material::uuid` | `N + Brand:uuid + Material::name` | `616fc86d-7d99-4953-96c7-46d2836b9be9` |
| `MaterialPackage::uuid` | `N + Brand::uuid + MaterialPackage::gtin` | `6f7d485e-db8d-4979-904e-a231cd6602b2` |
| `MaterialPackageInstance::uuid` | `N + (NFC tag UID)` | `31062f81-b5bd-4f86-a5f8-46367e841508` |

For example:
{% python %}
import uuid

def generate_uuid(namespace, *args):
   return uuid.uuid5(uuid.UUID(namespace), b"".join(args))

brand_namespace = "5269dfb7-1559-440a-85be-aba5f3eff2d2"
brand_name = "Prusament"
brand_uuid = generate_uuid(brand_namespace, brand_name.encode("utf-8"))
print(f"brand_uuid = {brand_uuid}")

material_namespace = "616fc86d-7d99-4953-96c7-46d2836b9be9"
material_name = "PLA Prusa Galaxy Black"
material_uuid = generate_uuid(material_namespace, brand_uuid.bytes, material_name.encode("utf-8"))
print(f"material_uuid = {material_uuid}")

material_package_namespace = "6f7d485e-db8d-4979-904e-a231cd6602b2"
gtin = "1234"
material_package_uuid = generate_uuid(material_package_namespace, brand_uuid.bytes, gtin.encode("utf-8"))
print(f"material_package_uuid = {material_package_uuid}")

material_package_instance_namespace = "31062f81-b5bd-4f86-a5f8-46367e841508"
nfc_tag_uid = b"\xE0\x04\x01\x08\x66\x2F\x6F\xBC"
material_package_instance_uuid = generate_uuid(material_package_instance_namespace, nfc_tag_uid)
print(f"material_package_instance_uuid = {material_package_instance_uuid}")

palette_color_namespace = "6c10f945-d488-40aa-8a7e-d6d0bcacaccb"
palette_name = "pantone"
palette_color_name = "14-0225 TCX"
palette_color_uuid = generate_uuid(material_namespace, palette_name.encode("utf-8"), palette_color_name.encode("utf-8"))
print(f"palette_color_uuid = {palette_color_uuid}")
{% endpython %}
