"""Read pyproject.toml, write requirements.txt."""  # noqa: INP001

import tomllib
from pathlib import Path

p_in = Path(__file__).parent.parent / "pyproject.toml"
p_out = Path(__file__).parent.parent / "requirements.txt"

with p_in.open("rb") as fh:
    o = tomllib.load(fh)

lst = sorted(o["project"]["dependencies"], key=str.casefold)
p_out.write_text(
    "# created by gen_requirements.py from pyproject.toml\n" + "\n".join(lst) + "\n"
)
