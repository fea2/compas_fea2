from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Optional

from compas.geometry import Frame

from compas_fea2.base import FEAData
from compas_fea2.base import Frameable
from compas_fea2.base import Registry
from compas_fea2.base import from_data

if TYPE_CHECKING:
    pass


class GeneralDisplacement(FEAData, Frameable):
    """General imposed displacement.

    Represents imposed displacements or restraints on degrees of freedom
    in a local coordinate frame. Supports translation and rotation components.

    Parameters
    ----------
    x, y, z : bool, optional
        Translational displacement restraints along local x, y, z axes.
    xx, yy, zz : bool, optional
        Rotational displacement restraints about local x, y, z axes.
    frame : Frame or None, optional
        Local coordinate frame for the displacement.

    Notes
    -----
    This class only handles boolean restraint flags and an optional local frame.
    There are no numeric magnitudes to unit-normalize here, so no units decorator is applied.
    """

    __doc__ = __doc__ or ""

    DOF_MASK: Dict[str, bool] | None = None

    def __init__(self, x: bool = False, y: bool = False, z: bool = False, xx: bool = False, yy: bool = False, zz: bool = False, frame: Frame | None = None, **kwargs):
        FEAData.__init__(self, **kwargs)
        Frameable.__init__(self, frame=frame)
        self._x = x
        self._y = y
        self._z = z
        self._xx = xx
        self._yy = yy
        self._zz = zz

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data.update(
            {
                "frame": self._frame_data(),
                "x": self._x,
                "y": self._y,
                "z": self._z,
                "xx": self._xx,
                "yy": self._yy,
                "zz": self._zz,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls: type["GeneralDisplacement"], data: dict, registry: Optional[Registry] = None, duplicate=True) -> "GeneralDisplacement":
        frame_obj = None
        frame_data = data.get("frame")
        if frame_data:
            try:
                # Try compas Frame deserialization patterns
                if hasattr(Frame, "__from_data__"):
                    frame_obj = Frame.__from_data__(frame_data)  # type: ignore[attr-defined]
                elif hasattr(Frame, "from_data"):
                    frame_obj = Frame.from_data(frame_data)  # type: ignore[attr-defined]
            except Exception:
                frame_obj = None
        frame: Frame | None = frame_obj if isinstance(frame_obj, Frame) else None
        bc = cls(frame=frame)
        bc._x = data.get("x", False)
        bc._y = data.get("y", False)
        bc._z = data.get("z", False)
        bc._xx = data.get("xx", False)
        bc._yy = data.get("yy", False)
        bc._zz = data.get("zz", False)
        mask = getattr(cls, "DOF_MASK", None)
        if mask:
            for k, v in mask.items():
                setattr(bc, f"_{k}", v)
        return bc

    def __add__(self, other: "GeneralDisplacement") -> "GeneralDisplacement":
        """Combine two boundary conditions by OR-ing their component restraints.

        Parameters
        ----------
        other : GeneralDisplacement
            Another GeneralDisplacement instance to combine with.

        Returns
        -------
        GeneralDisplacement
            Combined displacement with OR-ed restraint components.

        Raises
        ------
        ValueError
            If the frames of the two displacements differ.
        """
        if not isinstance(other, GeneralDisplacement):
            return NotImplemented
        if self.frame != other.frame:
            raise ValueError(f"Cannot combine BCs with different frame: {self.frame!r} vs {other.frame!r}")
        combined = GeneralDisplacement(
            x=self.x or other.x,
            y=self.y or other.y,
            z=self.z or other.z,
            xx=self.xx or other.xx,
            yy=self.yy or other.yy,
            zz=self.zz or other.zz,
            frame=self._frame,
        )
        return combined

    @property
    def x(self) -> bool:
        """Return the local x restraint boolean."""
        return self._x

    @property
    def y(self) -> bool:
        """Return the local y restraint boolean."""
        return self._y

    @property
    def z(self) -> bool:
        """Return the local z restraint boolean."""
        return self._z

    @property
    def xx(self) -> bool:
        """Return the local xx restraint boolean."""
        return self._xx

    @property
    def yy(self) -> bool:
        """Return the local yy restraint boolean."""
        return self._yy

    @property
    def zz(self) -> bool:
        """Return the local zz restraint boolean."""
        return self._zz

    @property
    def components(self) -> Dict[str, Any]:
        """Return the local restraint booleans.

        Returns
        -------
        dict
            Dictionary of local restraint booleans keyed by component names.
        """
        return {c: getattr(self, c) for c in ["x", "y", "z", "xx", "yy", "zz"]}

    @property
    def global_components(self) -> Dict[str, bool]:
        """Return the global (uppercase) restraint booleans.

        Returns
        -------
        dict
            Dictionary of global restraint booleans keyed by component names.
        """
        return {c: getattr(self, c) for c in ["X", "Y", "Z", "XX", "YY", "ZZ"]}

    def _global_axis_restrained(self, axis: str, tol: float = 1e-12) -> bool:
        from compas.geometry import Vector

        # Fast path if local == global
        if not self.has_local_frame or self.is_axis_aligned():
            mapping = {"X": self._x, "Y": self._y, "Z": self._z, "XX": self._xx, "YY": self._yy, "ZZ": self._zz}
            return mapping[axis]
        lx, ly, lz = self.direction_cosines()  # local axes as global vectors
        if axis in ("X", "Y", "Z"):
            g = {"X": Vector(1, 0, 0), "Y": Vector(0, 1, 0), "Z": Vector(0, 0, 1)}[axis]
            coeffs = [g.dot(lx), g.dot(ly), g.dot(lz)]
            flags = [self._x, self._y, self._z]
        else:  # rotational analogous mapping
            g = {"XX": Vector(1, 0, 0), "YY": Vector(0, 1, 0), "ZZ": Vector(0, 0, 1)}[axis]
            coeffs = [g.dot(lx), g.dot(ly), g.dot(lz)]
            flags = [self._xx, self._yy, self._zz]
        for c, f in zip(coeffs, flags):
            if abs(c) > tol and not f:
                return False
        return True

    @property
    def X(self) -> bool:
        """Return the global X restraint boolean."""
        return self._global_axis_restrained("X")

    @property
    def Y(self) -> bool:
        """Return the global Y restraint boolean."""
        return self._global_axis_restrained("Y")

    @property
    def Z(self) -> bool:
        """Return the global Z restraint boolean."""
        return self._global_axis_restrained("Z")

    @property
    def XX(self) -> bool:
        """Return the global XX restraint boolean."""
        return self._global_axis_restrained("XX")

    @property
    def YY(self) -> bool:
        """Return the global YY restraint boolean."""
        return self._global_axis_restrained("YY")

    @property
    def ZZ(self) -> bool:
        """Return the global ZZ restraint boolean."""
        return self._global_axis_restrained("ZZ")

    def global_constraint_equations(self) -> list[tuple[Dict[str, float], float]]:
        """Return linear constraint equations in global translational DOFs implied by local restraints.

        Each equation corresponds to a local restrained translational DOF.
        Equation format: ( { 'UX': a, 'UY': b, 'UZ': c }, 0.0 ) meaning
        a*UX + b*UY + c*UZ = 0.

        Returns
        -------
        list of tuple of (dict, float)
            List of tuples each containing a dictionary mapping global DOF names to coefficients,
            and a float representing the right-hand side (always zero).

        Notes
        -----
        The coefficients are unitless as they represent direction cosines.
        Rotational mapping can be extended similarly when needed.
        """
        eqs: list[tuple[Dict[str, float], float]] = []
        if not any([self._x, self._y, self._z]):
            return eqs
        lx, ly, lz = self.direction_cosines()
        eq_map = [(self._x, lx), (self._y, ly), (self._z, lz)]
        for flag, vec in eq_map:
            if flag:
                eqs.append(({"UX": float(vec.x), "UY": float(vec.y), "UZ": float(vec.z)}, 0.0))
        return eqs
