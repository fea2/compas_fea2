from typing import Optional

from compas.geometry import Frame

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data
from compas_fea2.base import Frameable


class _Load(FEAData):
    """Initialises base _Load object.

    Parameters
    ----------
    amplitude :  :class:`compas_fea2.problem.Amplitude`
        Amplitude associated to the load, optionnal.

    Attributes
    ----------
    amplitude :  :class:`compas_fea2.problem.Amplitude`
        Amplitude associated to the load, optionnal.

    field : :class:`compas_fea2.problem.LoadField`
        Field associated with the load.

    step : :class:`compas_fea2.problem.Step`
        Step associated with the load.

    problem : :class:`compas_fea2.problem.Problem`
        Problem associated with the load.

    model : :class:`compas_fea2.model.Model`
        Model associated with the load.

    name : str
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    """

    def __init__(self, amplitude=None, **kwargs):
        super().__init__(**kwargs)
        self._amplitude = amplitude
        
    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "amplitude": self._amplitude,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        amplitude = data.get("amplitude")
        return cls(amplitude=amplitude, **data)

    @property
    def amplitude(self):
        return self._amplitude

    @property
    def field(self):
        return self._registration

    @property
    def step(self):
        if not self.field:
            raise ValueError("The load must be associated with a field.")
        return self.field._registration

    @property
    def problem(self):
        return self.step._registration

    @property
    def model(self):
        return self.problem._registration


class ScalarLoad(_Load):
    """Scalar load object.

    Parameters
    ----------
    scalar_load : float
        Scalar value of the load.

    amplitude :  :class:`compas_fea2.problem.Amplitude`
        Amplitude associated to the load, optionnal.

    Attributes
    ----------
    scalar_load : float
        Scalar value of the load

    amplitude :  :class:`compas_fea2.problem.Amplitude`
        Amplitude associated to the load, optionnal.
    """

    def __init__(self, scalar_load, amplitude=None, **kwargs):
        super().__init__(amplitude=amplitude, **kwargs)
        if not (isinstance(scalar_load, (int, float))):
            raise ValueError("The scalar_load must be a float.")
        self._scalar_load = scalar_load

    @property
    def scalar_load(self):
        return self._scalar_load


class VectorLoad(_Load, Frameable):
    """Vector load object.

    Parameters
    ----------
    x, y, z : float, optional
        Local force components along the local frame axes.
    xx, yy, zz : float, optional
        Local moment components about the local frame axes.
    frame : :class:`compas.geometry.Frame`, optional
        Local reference frame. If None, global frame is assumed (local == global).
    amplitude : :class:`compas_fea2.problem.Amplitude`, optional
        Amplitude associated to the load.

    Notes
    -----
    - Lowercase (x, y, z, xx, yy, zz) are ALWAYS stored as LOCAL components.
    - Uppercase (X, Y, Z, XX, YY, ZZ) expose the corresponding GLOBAL components
      obtained via the base Frameable transformations.
    """

    def __init__(self, x=None, y=None, z=None, xx=None, yy=None, zz=None, frame=None, **kwargs):
        _Load.__init__(self, **kwargs)
        Frameable.__init__(self, frame)
        self.x = x
        self.y = y
        self.z = z
        self.xx = xx
        self.yy = yy
        self.zz = zz

    @property
    def __data__(self):
        data = super().__data__
        data.update({
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "xx": self.xx,
            "yy": self.yy,
            "zz": self.zz,
            "frame": self._frame_data(),
        })
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
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
        return cls(
            x=data.get("x"),
            y=data.get("y"),
            z=data.get("z"),
            xx=data.get("xx"),
            yy=data.get("yy"),
            zz=data.get("zz"),
            frame=frame,
            amplitude=data.get("amplitude"),
            name=data.get("name"),
            uid=data.get("uid") if duplicate else None,
        )

    # --- arithmetic on LOCAL components --------------------------------
    def __mul__(self, scalar):
        for attr in ["x", "y", "z", "xx", "yy", "zz"]:
            val = getattr(self, attr)
            if val is not None:
                setattr(self, attr, val * scalar)
        return self

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __add__(self, other):
        if not isinstance(other, VectorLoad):
            raise TypeError("Can only add VectorLoad objects.")
        for attr in ["x", "y", "z", "xx", "yy", "zz"]:
            a = getattr(self, attr)
            b = getattr(other, attr)
            if a is not None and b is not None:
                setattr(self, attr, a + b)
        return self

    # --- local components dict -----------------------------------------
    @property
    def components(self):
        return {i: getattr(self, i) for i in ["x", "y", "z", "xx", "yy", "zz"]}

    @components.setter
    def components(self, value):
        iterator = value.items() if isinstance(value, dict) else value
        for k, v in iterator:
            setattr(self, k, v)

    # --- global transformation helpers (uppercase) ---------------------
    def _locals_to_global(self, triplet):
        """Helper to convert a local (x,y,z) numeric triplet to global tuple using Frameable.
        None values are treated as 0. Returns (gx, gy, gz) or (None,None,None) if all None.
        """
        if triplet is None or all(c is None for c in triplet):
            return (None, None, None)
        from compas.geometry import Vector
        lx, ly, lz = (c if c is not None else 0.0 for c in triplet)
        vec = Vector(lx, ly, lz)
        if self.has_local_frame:
            vec = self.to_global_vector(vec)
        return (vec.x, vec.y, vec.z)

    # Global force components
    @property
    def X(self):
        return self._locals_to_global((self.x, self.y, self.z))[0]

    @property
    def Y(self):
        return self._locals_to_global((self.x, self.y, self.z))[1]

    @property
    def Z(self):
        return self._locals_to_global((self.x, self.y, self.z))[2]

    # Global moment components
    @property
    def XX(self):
        return self._locals_to_global((self.xx, self.yy, self.zz))[0]

    @property
    def YY(self):
        return self._locals_to_global((self.xx, self.yy, self.zz))[1]

    @property
    def ZZ(self):
        return self._locals_to_global((self.xx, self.yy, self.zz))[2]

    @property
    def global_components(self):
        return {
            "X": self.X,
            "Y": self.Y,
            "Z": self.Z,
            "XX": self.XX,
            "YY": self.YY,
            "ZZ": self.ZZ,
        }
