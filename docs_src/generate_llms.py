import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import docs_src.vars as vars
from mcp_server.data_loader import load_all
from mcp_server.renderer import render_llms_txt, render_llms_full_txt


def generate(out_dir: str | None = None) -> None:
    entity_yamls, enum_yamls = load_all()
    target = pathlib.Path(out_dir or vars.out_dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / "llms.txt").write_text(render_llms_txt(entity_yamls, enum_yamls), encoding="utf-8")
    (target / "llms-full.txt").write_text(render_llms_full_txt(entity_yamls, enum_yamls), encoding="utf-8")


if __name__ == "__main__":
    generate()
