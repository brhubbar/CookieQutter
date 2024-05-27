"""Create 3-D printable cookie-cutters from a vector drawing with CadQuery."""

from sys import argv

from cookie_qutter.from_dxf import main


def entrypoint() -> None:
    """CLI Entrypoint."""
    main(argv[1])
