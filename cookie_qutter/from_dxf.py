"""
Create a cookie-cutter STL from a DXF.

Steps:

- Create an outline in Inkscape
- Draw the outer bound first.
- Export a copy as an R12 DXF
- Import into QCAD; correct scaling and positioning
    - Check for loops and disconnected nodes
- Export as R27 DXF from QCAD
- Feed into this program with `python cc_from_dxf filename.dxf`

"""

import logging
import sys
from os import environ
from pathlib import Path
from typing import Optional

import cadquery as cq

logging.basicConfig()
log = logging.getLogger(__name__)
if environ.get("DEBUG"):
    log.setLevel(10)
else:
    log.setLevel(20)

# Horizontal/in-plane dimensions measured outward from the provided boundary.
offsets = {
    "handle": 4,
    "spine": 1.2,
    "edge": 0.8,
}
# Vertical/out-of-plane dimensions measured from the print bed.
heights = {
    "handle": 2,
    "spine": 12,
    "edge": 20,
}

# Tolerance for edges. Make it half of the printer resolution (0.4mm nozzle)
tolerance = 0.4 / 2


def main(dxf: Path, stl: Optional[Path] = None) -> Path:
    """
    Process a DXF into a cookiecutter.

    Parameters
    ----------
    dxf : pathlib.Path
        Path to the DXF to convert to a cookie cutter.
    stl : pathlib.Path (optional)
        Path to save the resulting STL at. If not provided, defaults to `dxf`
        with the extension swapped for '.stl'.

    Returns
    -------
    pathlib.Path
        The path to the STL.

    """
    dxf = Path(dxf).absolute()
    stl = stl or dxf.with_suffix(".stl")

    original_wires = cq.importers.importDXF(dxf, tol=tolerance)._collectProperty(
        "Wires"
    )

    cookie_cutter = cq.Workplane()

    for wire in original_wires:
        log.debug("Processing %s", wire)
        log.info("Wire area: %4.2d mm^2", cq.Face.makeFromWires(wire).Area())
        try:
            # Assume the first wire is the only exterior wire.
            cutter_part = cutterify(wire)
        except ValueError:
            log.exception(
                "A wire failed to cutterify. Check for loops or disjointed nodes in QCAD (zoom way in)."  # noqa: E501
            )
            _create_debug_brep(wire, stl.parent)
            log.info("Continuing without a wire.")
            continue
        cookie_cutter.add(cutter_part)

    log.debug("Exporting to %s", stl)
    if not cookie_cutter.findSolid().exportStl(str(stl)):
        log.error("STL export failed.")
        _create_debug_brep(wire, stl.parent)
        raise RuntimeError("STL export failed.")
    return stl


def cutterify(wire: cq.Wire) -> cq.Solid:
    """Convert a wire into a cookiecutter."""
    wire = wire.mirror("YZ")
    original_edges = cq.Workplane(wire)
    handle_edges = (
        original_edges.edges()
        .toPending()
        .offset2D(offsets["handle"], "arc")
        .extrude(heights["handle"])
        .findSolid()
    )

    spine_edges = (
        original_edges.edges()
        .toPending()
        .offset2D(offsets["spine"], "arc")
        .extrude(heights["spine"])
        .findSolid()
    )

    edge_edges = (
        original_edges.edges()
        .toPending()
        .offset2D(offsets["edge"], "arc")
        .extrude(heights["edge"])
        .findSolid()
    )

    compound = handle_edges.fuse(spine_edges, edge_edges)

    # This ends up being half the height because half of the box extends below
    # the plane and gets intersected away.
    support_bar = (
        original_edges.box(500, 10, heights["handle"]).findSolid().intersect(compound)
    )

    return (
        original_edges.wires()
        .toPending()
        .add(compound)
        .extrude(heights["edge"], combine="cut")
        .findSolid()
        .fuse(support_bar)
    )


def _create_debug_brep(wire: cq.Wire, folder: Path):
    debug_filename = Path(folder, "debug.brep")
    log.info("Creating %s for debugging", debug_filename)
    debug_views = [wire]
    for offset in [-5, -1, -0.1, 0.1, 1, 5]:
        try:
            debug_views.extend(wire.offset2D(offset, "arc"))
        except ValueError:
            log.debug("Failed to offset with %smm", offset)
            continue
    debug_compound = cq.Compound.makeCompound(debug_views)
    debug_compound.exportBrep(str(debug_filename))


if __name__ == "__main__":
    main(sys.argv[1])
