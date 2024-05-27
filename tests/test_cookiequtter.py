"""
Test that the cookiequtter algorithms do what I'd expect.

https://en.wikipedia.org/wiki/Test-driven_development
https://www.agileinstitute.com/articles/dispelling-myths-about-test-driven-development

TL;DR: "Writing the tests first: The tests should be written before the
functionality that is to be tested. This has been claimed to have many benefits.
It helps ensure that the application is written for testability, as the
developers must consider how to test the application from the outset rather than
adding it later."

"""

# Assert statements are fine in testing.
# ruff: noqa: S101
# Docstrings and annotations aren't usually needed for tests.
# ruff: noqa: D103, D400, D401, ANN201
# I'm alright with long lines here.
# ruff: noqa: E501

# From pytest: tmp_path

from pathlib import Path

import cadquery as cq

from cookie_qutter import from_dxf as sut

TEST_DIR = Path(__file__).parent
TEST_FILES = Path(TEST_DIR, "test_files")


def test_good_runs_well(tmp_path):
    args = (Path(TEST_FILES, "nefarious_loop_fixed.dxf"), Path(tmp_path, "good.stl"))
    unexpected = Path(tmp_path, "debug.brep")

    result = sut.main(*args)

    assert result == args[1]
    assert result.is_file()
    # File should create without complaints.
    assert not unexpected.is_file()


def test_bad_debugs(tmp_path):
    args = (Path(TEST_FILES, "nefarious_loop.dxf"), Path(tmp_path, "bad.stl"))
    expected = Path(tmp_path, "debug.brep")

    result = sut.main(*args)

    assert result == args[1]
    # We still create a best-effort stl.
    assert result.is_file()
    # The bad wire causes a debug brep to be created for viewing.
    assert expected.is_file()
