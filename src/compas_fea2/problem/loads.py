from compas_fea2.base import FEAData

# TODO: make units independent using the utilities function

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
    def __init__(self, amplitude = None, **kwargs):
        super().__init__(**kwargs)
        self._amplitude = amplitude
    
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
    def __init__(self, scalar_load, amplitude = None, **kwargs):
        super().__init__(amplitude=amplitude, **kwargs)
        if not(isinstance(scalar_load, (int,float))) :
            raise ValueError("The scalar_load must be a float.")
        self._scalar_load = scalar_load
    
    @property
    def scalar_load(self):
        return self._scalar_load


class VectorLoad(_Load):
    """Vector load object.

    Parameters
    ----------
    axes : str, "local" or "global"
        The load is either defined in the local frame or the global one.
        If not indicated, the global frame is considered.

    x : float
        x-axis force value of the load.
    y : float
        y-axis force value of the load.
    z : float
        z-axis force value of the load.
    xx : float
        Moment value of the load about the x-axis. 
    yy : float
        Moment value of the load about the y-axis. 
    zz : float
        Moment value of the load about the z-axis.
    amplitude :  :class:`compas_fea2.problem.Amplitude`
        Amplitude associated to the load, optionnal.  

    Attributes
    ----------
    axes : str, "local" or "global"
        The load is either defined in the local frame or the global one.
        If not indicated, the global frame is considered.
    x : float
        x-axis force value of the load.
    y : float
        y-axis force value of the load.
    z : float
        z-axis force value of the load.
    xx : float
        Moment value of the load about the x-axis. 
    yy : float
        Moment value of the load about the y-axis. 
    zz : float
        Moment value of the load about the z-axis.
    amplitude :  :class:`compas_fea2.problem.Amplitude`
        Amplitude associated to the load, optionnal.  
    components : {str: float}
        Dictionnary of the components of the load and values
    """

    def __init__(self, x=None, y=None, z=None, xx=None, yy=None, zz=None, axes="global", **kwargs):
        super(VectorLoad, self).__init__(**kwargs)
        self.axes = axes
        self.x = x
        self.y = y
        self.z = z
        self.xx = xx
        self.yy = yy
        self.zz = zz
        
    def __mul__(self, scalar):
        """Multiply the load by a scalar."""
        for attr in ["x", "y", "z", "xx", "yy", "zz"]:
            if getattr(self, attr) is not None:
                setattr(self, attr, getattr(self, attr) * scalar)
        return self
    
    def __rmul__(self, scalar):
        """Multiply the load by a scalar."""
        return self.__mul__(scalar)
    
    def __add__(self, other):
        """Add two VectorLoad objects."""
        if not isinstance(other, VectorLoad):
            raise TypeError("Can only add VectorLoad objects.")
        for attr in ["x", "y", "z", "xx", "yy", "zz"]:
            if getattr(self, attr) is not None and getattr(other, attr) is not None:
                setattr(self, attr, getattr(self, attr) + getattr(other, attr))
        return self

    @property
    def components(self):
        return {i: getattr(self, i) for i in ["x", "y", "z", "xx", "yy", "zz"]}

    @components.setter
    def components(self, value):
        for k, v in value:
            setattr(self, k, v)


class HeatFluxLoad(ScalarLoad):
    """ Heat flux load for heat analysis.
    
    Parameters
    ----------
    q : float
        Heat flux value of the load.
    
    amplitude :  :class:`compas_fea2.problem.Amplitude`
        Amplitude associated to the load, optionnal.  

    Attributes
    ----------
    q : float
        Heat flux value of the load.
    
    amplitude :  :class:`compas_fea2.problem.Amplitude`
        Amplitude associated to the load, optionnal. 
    """

    def __init__(self, q, amplitude = None,  **kwargs):
        super().__init__(scalar_load=q, amplitude=amplitude, **kwargs)
    
    @property
    def q(self):
        return self._scalar_load
    
class TemperatureLoad(ScalarLoad):
    """ Temperature load for heat analysis
    
    Parameters
    ----------
    temperature : float
        Value of the temperature load.
    
    amplitude :  :class:`compas_fea2.problem.Amplitude`
        Amplitude associated to the load, optionnal.  

    Attributes
    ----------
    temperature : float
        Value of the temperature load.
    
    amplitude :  :class:`compas_fea2.problem.Amplitude`
        Amplitude associated to the load, optionnal. 
    """

    def __init__(self, temperature, amplitude = None, **kwargs):
        super().__init__(scalar_load=temperature, amplitude=amplitude, **kwargs)
    
    @property
    def temperature(self):
        return self._scalar_load
