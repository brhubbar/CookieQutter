"""
Create a cookie-cutter from a DXF.

Steps:

- Create an outline in Inkscape
- Import into QCAD; correct scaling and positioning
- Feed into this program

"""

import sys
from pathlib import Path

import cadquery as cq

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


def main(dxf: Path):
    dxf = Path(dxf)
    original_edges = cq.importers.importDXF(dxf, tol=tolerance)

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

    cookie_cutter = (
        original_edges.wires()
        .toPending()
        .add(compound)
        .extrude(heights["edge"], combine="cut")
        .findSolid()
    )

    cookie_cutter.exportStl(str(dxf.with_suffix(".stl")))


if __name__ == "__main__":
    main(sys.argv[1])
