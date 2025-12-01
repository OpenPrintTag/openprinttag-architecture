import typing
import io


def default_transform(data: any):
    match data:
        case None:
            return ""

        case bool():
            return "yes" if data else "no"

        case list():
            return "<br>".join(str(x) for x in data)

        case _:
            return str(data)


def required_transform(data: any):
    match data:
        case True:
            return "❗"

        case False | None:
            return ""

        case "recommended":
            return "❕"

        case _:
            assert False, f"Unknown required value '{data}'"


class Column(typing.NamedTuple):
    field: str
    title: str
    transform: any = default_transform
    transform_ext: any = None


def generate_table(data, columns: typing.List[Column], filter: any = None):
    tgt = io.StringIO("")

    # Generate table header
    tgt.write("|")
    for col in columns:
        tgt.write(col.title + "|")
    tgt.write("\n")

    tgt.write("|")
    for col in columns:
        tgt.write(":--|")
    tgt.write("\n")

    for row in data:
        if filter and not filter(row):
            continue

        tgt.write("|")
        for col in columns:
            cell = row.get(col.field, None)

            if col.transform_ext:
                cell = col.transform_ext(cell, row)
            else:
                cell = col.transform(cell)

            tgt.write(cell)
            tgt.write("|")
        tgt.write("\n")

    tgt.write("\n")

    return tgt.getvalue()
