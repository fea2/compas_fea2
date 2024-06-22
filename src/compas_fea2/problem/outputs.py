from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from itertools import chain

from compas_fea2.base import FEAData


class _Output(FEAData):
    """Base class for output requests.

    Parameters
    ----------
    FEAData : _type_
        _description_

    Notes
    -----
    Outputs are registered to a :class:`compas_fea2.problem.Step`.

    """

    @property
    def __data__(self):
        return {}

    @classmethod
    def __from_data__(cls, data):
        return cls()

    def __init__(self, **kwargs):
        super(_Output, self).__init__(**kwargs)

    @property
    def step(self):
        return self._registration

    @property
    def problem(self):
        return self.step._registration

    @property
    def model(self):
        return self.problem._registration


class FieldOutput(_Output):
    """FieldOutput object for specification of the fields (stresses, displacements,
    etc..) to output from the analysis.

    Parameters
    ----------
    nodes_outputs : list
        list of node fields to output
    elements_outputs : list
        list of elements fields to output

    Attributes
    ----------
    name : str
        Automatically generated id. You can change the name if you want a more
        human readable input file.
    nodes_outputs : list
        list of node fields to output
    elements_outputs : list
        list of elements fields to output

    """

    @property
    def __data__(self):
        return {
            "node_outputs": self.node_outputs,
            "element_outputs": self.element_outputs,
            "contact_outputs": self.contact_outputs,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            node_outputs=data["node_outputs"],
            element_outputs=data["element_outputs"],
            contact_outputs=data["contact_outputs"],
        )

    def __init__(self, node_outputs=None, element_outputs=None, contact_outputs=None, **kwargs):
        super(FieldOutput, self).__init__(**kwargs)
        self._node_outputs = node_outputs
        self._element_outputs = element_outputs
        self._contact_outputs = contact_outputs

    @property
    def node_outputs(self):
        return self._node_outputs

    @property
    def element_outputs(self):
        return self._element_outputs

    @property
    def contact_outputs(self):
        return self._contact_outputs

    @property
    def outputs(self):
        return chain(self.node_outputs, self.element_outputs, self.contact_outputs)


class HistoryOutput(_Output):
    """HistoryOutput object for recording the fields (stresses, displacements,
    etc..) from the analysis.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.

    Attributes
    ----------
    name : str
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.

    """

    @property
    def __data__(self):
        return {}

    @classmethod
    def __from_data__(cls, data):
        return cls()

    def __init__(self, **kwargs):
        super(HistoryOutput, self).__init__(**kwargs)
