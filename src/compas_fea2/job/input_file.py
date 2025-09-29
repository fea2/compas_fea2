import os
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Optional
from typing import Union

from compas_fea2.base import FEAData
from compas_fea2.config import settings

if TYPE_CHECKING:
    from compas_fea2.model import Model
    from compas_fea2.problem import Problem


class InputFile(FEAData):
    """Input file object for standard FEA.

    Parameters
    ----------
    name : str, optional
        Unique identifier. If not provided, it is automatically generated. Set a
        name if you want a more human-readable input file.

    Attributes
    ----------
    name : str
        Unique identifier.
    problem : :class:`compas_fea2.problem.Problem`
        The problem to generate the input file from.
    model : :class:`compas_fea2.model.Model`
        The model associated with the problem.
    path : str
        Complete path to the input file.

    """

    _registration: "Problem"
    _extension: Optional[str]
    path: Optional[str]

    def __init__(self, problem: "Problem", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._registration = problem
        self._extension = None
        self.path = None

    @property
    def file_name(self) -> str:
        return "{}.{}".format(self.problem.name, self._extension)

    @property
    def problem(self) -> "Problem":
        return self._registration

    @property
    def model(self) -> "Model | None":
        if self.problem:
            return self.problem._registration

    # ==============================================================================
    # General methods
    # ==============================================================================

    def write_to_file(self, path: Optional[Union[str, Path]] = None) -> str:
        """Writes the InputFile to a file in a specified location.

        Parameters
        ----------
        path : str, optional
            Path to the folder where the input file will be saved, by default
            ``None``. If not provided, the Problem path attributed is used.

        Returns
        -------
        str
            Information about the results of the writing process.

        """
        path = str(path or self.problem.path)
        if not path:
            raise ValueError("A path to the folder for the input file must be provided")
        file_path = os.path.join(path, self.file_name)
        content = self.jobdata
        if not content:
            raise ValueError("No content to write to the input file.")
        with open(file_path, "w") as f:
            f.writelines(content)
        if settings.VERBOSE:
            print("Input file generated in the following location: {}".format(file_path))
        return content


class ParametersFile(InputFile):
    """Input file object for Optimizations."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        raise NotImplementedError
