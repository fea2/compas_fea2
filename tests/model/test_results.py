from compas_fea2.results.fields import DisplacementFieldResults
from compas_fea2.problem import _Step


def test_displacement_field_results():
    """Test the DisplacementFieldResults class."""
    # Create a mock step object
    step = _Step(name="test_step")

    # Create an instance of DisplacementFieldResults
    results = DisplacementFieldResults(step)

    # Check if the instance is created correctly
    assert results._registration == step
    assert results.step.name == "test_step"
    assert results.sqltable_schema == {
        "table_name": "u",
        "columns": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("key", "INTEGER"),
            ("step", "TEXT"),
            ("part", "TEXT"),
            ("x", "REAL"),
            ("y", "REAL"),
            ("z", "REAL"),
            ("rx", "REAL"),
            ("ry", "REAL"),
            ("rz", "REAL"),
        ],
    }
