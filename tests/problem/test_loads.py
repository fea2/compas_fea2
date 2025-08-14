import pytest
from pathlib import Path

from compas.geometry import Frame

from .conftest import load_module_from_path, problem_src_dir


def _mod():
    return load_module_from_path(
        "compas_fea2.problem.loads_test", problem_src_dir() / "loads.py"
    )


def test_scalar_load_init_and_value():
    loads = _mod()
    s = loads.ScalarLoad(5.5)
    assert s.scalar_load == 5.5
    assert "amplitude" in s.__data__


def test_scalar_load_type_validation():
    loads = _mod()
    with pytest.raises(ValueError):
        loads.ScalarLoad("not-a-number")


def test_vector_load_local_and_global_without_frame():
    loads = _mod()
    v = loads.VectorLoad(x=1.0, y=2.0, z=3.0)
    assert v.components == {"x": 1.0, "y": 2.0, "z": 3.0, "xx": None, "yy": None, "zz": None}
    assert v.X == 1.0 and v.Y == 2.0 and v.Z == 3.0


def test_vector_load_global_with_rotated_frame_about_Z():
    loads = _mod()
    # Local x aligned to global +Y, local y aligned to global -X, local z = global +Z
    frame = Frame((0, 0, 0), (0, 1, 0), (-1, 0, 0))
    v = loads.VectorLoad(x=10.0, y=0.0, z=0.0, frame=frame)
    assert pytest.approx(v.X, abs=1e-12) == 0.0
    assert pytest.approx(v.Y, abs=1e-12) == 10.0
    assert pytest.approx(v.Z, abs=1e-12) == 0.0


def test_vector_load_mul_and_add_are_inplace():
    loads = _mod()
    a = loads.VectorLoad(x=1.0, y=2.0)
    b = loads.VectorLoad(x=3.0, y=5.0)
    a2 = a * 2.0
    assert a2 is a
    assert a.components["x"] == 2.0 and a.components["y"] == 4.0
    a_plus_b = a + b
    assert a_plus_b is a
    assert a.components["x"] == 5.0 and a.components["y"] == 9.0


def test_vector_load_data_roundtrip_without_frame():
    loads = _mod()
    v = loads.VectorLoad(x=1.0, y=2.0, z=3.0, xx=0.1, yy=0.2, zz=0.3)
    data = v.__data__
    v2 = loads.VectorLoad.__from_data__(data)
    assert v2.components == v.components
