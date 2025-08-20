import os
import sys
import shutil
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from typing import List
from typing import Optional
from typing import Union

from compas_fea2.base import FEAData
from compas_fea2.base import from_data

from compas_fea2.job.input_file import InputFile

from compas_fea2.results.database import ResultsDatabase


logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from compas_fea2.base import Registry
    from compas_fea2.model.model import Model
    from compas_fea2.problem.steps import _Step
    from compas_fea2.problem.steps import StaticStep
    from compas_fea2.problem.steps import DynamicStep
    from compas_fea2.problem.steps import HeatTransferStep

StepType = Union["StaticStep", "DynamicStep", "HeatTransferStep"]
    
    
class Problem(FEAData):
    """A Problem is a collection of analysis steps (:class:`compas_fea2.problem._Step)
    applied in a specific sequence.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    describption : str, optional
        Brief description of the Problem, , by default ``None``.
        This will be added to the input file and can be useful for future reference.

    Attributes
    ----------
    name : str
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    model : :class:`compas_fea2.model.Model`
        Model object to analyse.
    describption : str
        Brief description of the Problem. This will be added to the input file and
        can be useful for future reference.
    steps : list of :class:`compas_fea2.problem._Step`
        list of analysis steps in the order they are applied.
    path : str, :class:`pathlib.Path`
        Path to the analysis folder where all the files will be saved.
    path_db : str, :class:`pathlib.Path`
        Path to the SQLite database where the results are stored.
    results : :class:`compas_fea2.results.Results`
        Results object with the analyisis results.

    Notes
    -----
    Problems are registered to a :class:`compas_fea2.model.Model`.

    Problems can also be used as canonical `load combinations`, where each `load`
    is actually a `factored step`. For example, a typical load combination such
    as 1.35*DL+1.50LL can be applied to the model by creating the Steps DL and LL,
    factoring them (see :class:`compas_fea2.problem.Step documentation) and adding
    them to Problme

    While for linear models the sequence of the steps is irrelevant, it is not the
    case for non-linear models.

    Warnings
    --------
    Factore Steps are new objects! check the :class:`compas_fea2.problem._Step
    documentation.

    """

    def __init__(self, description: Optional[str] = None, **kwargs):
        super(Problem, self).__init__(**kwargs)
        self.description = description
        self._path = None
        self._steps: List[StepType] | None = None
        self._rdb = None

    @property
    def __data__(self) -> dict:
        base = super().__data__
        base.update(
            {
                "description": self.description,
                "path": str(self.path) if self.path else None,
                "steps": [s.__data__ for s in self._steps] if self._steps else None,
            }
        )
        return base

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional["Registry"] = None, duplicate=True) -> "Problem":
        if not registry:
            raise ValueError("A registry is required to create a Part from data.")
        description = data.get("description", "")
        problem = cls(description=description)
        problem._path = data.get("path", None)
        for step_data in data.get("steps", []):
            problem.add_step(registry.add_from_data(step_data, duplicate=duplicate))
        return problem

    @property
    def model(self) -> "Model | None":
        """Return the model associated with the problem."""
        return self._registration

    @property
    def steps(self) -> List[StepType] | None:
        """List of analysis steps in the order they are applied."""
        return self._steps

    @property
    def path(self) -> Optional[Path]:
        """Path to the analysis folder where all the files will be saved."""
        return self._path

    @path.setter
    def path(self, value: Union[str, Path]):
        """Set the path to the analysis folder where all the files will be saved."""
        self._path = value if isinstance(value, Path) else Path(value)
        # Keep the results database (if already created) in sync with the new path
        if self._rdb and hasattr(self._rdb, "db_uri"):
            self._rdb.db_uri = self.path_db

    @property
    def path_db(self) -> Optional[Path]:
        """Path to the SQLite database where the results are stored."""
        if not self._path:
            return None
        return Path(self._path) / f"{self.name}-results.db"

    @property
    def rdb(self) -> ResultsDatabase:
        """Return the results database associated with the problem.
        Defaults to the SQLite implementation, cached on first access.
        """
        # Ensure we have a valid DB path before instantiating
        if not self.path_db:
            raise ValueError("Problem path is not set. Set Problem.path or run analysis/extraction before accessing the results database.")
        # (Re)create the DB wrapper if it doesn't exist or if the path changed
        if self._rdb is None or getattr(self._rdb, "db_uri", None) != self.path_db:
            self._rdb = ResultsDatabase.sqlite(self)
        return self._rdb

    @rdb.setter
    def rdb(self, value: Union[str, ResultsDatabase]):
        """Set the results database associated with the problem.
        Pass one of the available factories on ResultsDatabase, e.g. "sqlite", "hdf5", "json",
        or provide an already-instantiated ResultsDatabase.
        """
        # Accept a ready instance
        if isinstance(value, ResultsDatabase):
            self._rdb = value
            # Ensure the instance has the current db path, if applicable
            if hasattr(self._rdb, "db_uri"):
                self._rdb.db_uri = self.path_db
            return
        # Accept a factory name
        if isinstance(value, str) and hasattr(ResultsDatabase, value):
            self._rdb = getattr(ResultsDatabase, value)(self)
            return
        raise ValueError("Invalid ResultsDatabase option")

    @property
    def input_file(self) -> InputFile:
        """Return the InputFile object that generates the input file."""
        return InputFile(self)

    # =========================================================================
    #                           Step methods
    # =========================================================================

    def find_step_by_name(self, name: str) -> StepType | None:
        """Find if there is a step with the given name in the problem.

        Parameters
        ----------
        name : str

        Returns
        -------
        :class:`compas_fea2.problem._Step`

        """
        if self._steps:
            for step in self._steps:
                if step.name == name:
                    return step

    def is_step_in_problem(self, step: StepType, add: bool = True) -> bool | StepType:
        """Check if a :class:`compas_fea2.problem._Step` is defined in the Problem.

        Parameters
        ----------
        step : :class:`compas_fea2.problem._Step`
            The Step object to find.

        Returns
        -------
        :class:`compas_fea2.problem._Step`

        Raises
        ------
        ValueError
            if `step` is a string and the step is not defined in the problem
        TypeError
            `step` must be either an instance of a `compas_fea2` Step class or the
            name of a Step already defined in the Problem.
        """
        from compas_fea2.problem.steps import _Step
        if not isinstance(step, _Step):
            raise TypeError("{!r} is not a Step".format(step))
        if self._steps:
            if step not in self._steps:
                print("{!r} not found".format(step))
                if add:
                    step = self.add_step(step)
                    print("{!r} added to the Problem".format(step))
                    return step
                return False
            return True
        else:
            return False

    def add_step(self, step: StepType) -> StepType:
        # # type: (_Step) -> Step
        """Adds a :class:`compas_fea2.problem._Step` to the problem. The name of
        the Step must be unique

        Parameters
        ----------
        Step : :class:`compas_fea2.problem._Step`
            The analysis step to add to the problem.

        Returns
        -------
        :class:`compas_fea2.problem._Step`
        """
        from compas_fea2.problem.steps import _Step
        if not isinstance(step, _Step):
            raise TypeError("You must provide a valid compas_fea2 Step object")
        if self.is_step_in_problem(step):
            raise ValueError("The step is already in the problem.")
        if self.find_step_by_name(step.name):
            raise ValueError("There is already a step with the same name in the model.")
        if not self._steps:
            self._steps = []
        step._key = len(self._steps)
        self._steps.append(step)
        step._registration = self
        return step

    def add_steps(self, steps: List[StepType]) -> List[StepType]:
        """Adds multiple :class:`compas_fea2.problem._Step` objects to the problem.

        Parameters
        ----------
        steps : list[:class:`compas_fea2.problem._Step`]
            List of steps objects in the order they will be applied.

        Returns
        -------
        list[:class:`compas_fea2.problem._Step`]
        """
        return [self.add_step(step) for step in steps]

    def add_static_step(self, **kwargs) -> "StaticStep":
        # # type: (_Step) -> Step
        """Adds a :class:`compas_fea2.problem._Step` to the problem. The name of
        the Step must be unique

        Parameters
        ----------
        Step : :class:`compas_fea2.problem.StaticStep`, optional
            The analysis step to add to the problem, by default None.
            If not provided, a :class:`compas_fea2.problem.StaticStep` with default
            attributes is created.

        Returns
        -------
        :class:`compas_fea2.problem._Step`
        """
        from compas_fea2.problem.steps import StaticStep
        step = StaticStep(**kwargs)
        return self.add_step(step)
    
    def add_linear_static_perturbation_step(self, lp_step: "LinearStaticPerturbation", base_step: str):
        """Add a linear perturbation step to a previously defined step.

        Parameters
        ----------
        lp_step : obj
            :class:`compas_fea2.problem.LinearPerturbation` subclass instance
        base_step : str
            name of a previously defined step which will be used as starting conditions
            for the application of the linear perturbation step.

        Notes
        -----
        Linear perturbartion steps do not change the history of the problem (hence
        following steps will not consider their effects).

        """
        raise NotImplementedError

    # ==============================================================================
    # Summary
    # ==============================================================================

    def summary(self) -> str:
        # type: () -> str
        """Prints a summary of the Problem object.

        Parameters
        ----------
        None

        Returns
        -------
        str
            Problem summary
        """
        steps_data = "\n".join([f"{step.name}" for step in (self._steps or [])])

        summary = f"""
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
compas_fea2 Problem: {self._name}
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

description: {self.description or "N/A"}

Steps (in order of application)
-------------------------------
{steps_data}

Analysis folder path : {self.path or "N/A"}

"""
        print(summary)
        return summary

    # =========================================================================
    #                         Analysis methods
    # =========================================================================
    def write_input_file(self, path: Optional[Union[Path, str]] = None) -> str:
        """Writes the input file.

        Parameters
        ----------
        path : :class:`pathlib.Path`
            Path to the folder where the input file is saved. In case the folder
            does not exist, one is created.

        Returns
        -------
        :class:`compas_fea2.job.InputFile`
            The InputFile objects that generates the input file.
        """
        path = path or self.path
        if not path:
            raise ValueError("A path to the folder for the input file must be provided")
        if not isinstance(path, Path):
            path = Path(path)
        if not path.exists():
            path.mkdir(parents=True)
        return self.input_file.write_to_file(path)

    def _check_analysis_path(self, path: Path, erase_data: Union[bool, str] = False) -> Path:
        """Check and prepare the analysis path, ensuring the correct folder structure.

        Parameters
        ----------
        path : :class:`pathlib.Path`
            Path where the input file will be saved.
        erase_data : bool | str, optional
            If True, automatically erase the folder's contents if it is recognized as an FEA2 results folder. Default is False.
            Pass "armageddon" to erase all contents without prompting even if the folder is not recognized as an FEA2 results folder.

        Returns
        -------
        :class:`pathlib.Path`
            Path where the input file will be saved.

        Raises
        ------
        ValueError
            If the folder is not a valid FEA2 results folder and `erase_data` is True but not confirmed by the user.
        """

        def _delete_folder_contents(folder_path: Path):
            """Helper method to delete all contents of a folder."""
            for entry in folder_path.iterdir():
                try:
                    if entry.is_dir():
                        shutil.rmtree(entry)
                    else:
                        entry.unlink()
                except FileNotFoundError:
                    # Entry may already be gone due to concurrent operations
                    pass

        if not isinstance(path, Path):
            path = Path(path)

        # Prepare the main and analysis paths
        if not self.model:
            raise ValueError(f"{self!r} is trying to access the model path but it is not registered to any model.")
        
        # Model folder and problem subfolder
        self.model._path = path
        self._path = self.model._path.joinpath(self.name)

        if self._path.exists():
            # Check if the folder contains FEA2 results
            try:
                entries = os.listdir(self._path)
            except FileNotFoundError:
                entries = []
            is_fea2_folder = any(fname.endswith("-results.db") for fname in entries)

            if is_fea2_folder:
                if erase_data is True:
                    _delete_folder_contents(self._path)
                else:
                    # keep existing contents
                    logger.debug("Reusing existing FEA2 folder at %s", self._path)
            else:
                # Folder exists but is not an FEA2 results folder
                if erase_data == "armageddon":
                    _delete_folder_contents(self._path)
                elif erase_data is True:
                    raise ValueError(
                        f"Folder {self._path} is not recognized as an FEA2 results folder. "
                        "Refusing to erase contents without 'armageddon'."
                    )
                else:
                    logger.debug("Existing non-FEA2 folder kept at %s", self._path)
        else:
            # Create the directory if it does not exist
            self._path.mkdir(parents=True, exist_ok=True)

        return self._path

    def analyse(self, path: Optional[Union[Path, str]] = None, erase_data: bool = False, *args, **kwargs):
        """Analyse the problem in the selected backend.

        Raises
        ------
        NotImplementedError
            This method is implemented only at the backend level.

        """
        # generate keys
        if not self.model:
            raise ValueError("Problem is not registered to any model.")
        # Prepare analysis folder
        analysis_root = Path(path) if path else (self.model._path or Path.cwd())
        self._check_analysis_path(analysis_root, erase_data=erase_data)
        # Ensure model members have keys
        self.model.assign_keys()
        raise NotImplementedError("this function is not available for the selected backend")

    def analyze(self, path: Optional[Union[Path, str]] = None, erase_data: bool = False, *args, **kwargs):
        """American spelling of the analyse method"""
        self.analyse(path=path, erase_data=erase_data, *args, **kwargs)

    def extract_results(self, path: Optional[Union[Path, str]] = None, erase_data: Optional[Union[bool, str]] = False, *args, **kwargs):
        """Extract the results from the native database system to SQLite.

        Parameters
        ----------
        path : :class:`pathlib.Path`
            Path to the folder where the results are saved.
        erase_data : bool, optional
            If True, automatically erase the folder's contents if it is recognized as an FEA2 results folder. Default is False.
            Pass "armageddon" to erase all contents of the folder without checking.

        Raises
        ------
        NotImplementedError
            This method is implemented only at the backend level.
        """
        if path:
            self._check_analysis_path(Path(path), erase_data=erase_data or False)
        elif not self._path:
            raise ValueError("Problem path is not set. Provide a path or set Problem.path before extracting results.")
        raise NotImplementedError("this function is not available for the selected backend")

    def analyse_and_extract(self, path: Optional[Union[Path, str]] = None, erase_data: bool = False, *args, **kwargs):
        """Analyse the problem in the selected backend and extract the results
        from the native database system to SQLite.

        Raises
        ------
        NotImplementedError
            This method is implemented only at the backend level.
        """
        if path:
            self._check_analysis_path(Path(path), erase_data=erase_data)
        elif not self._path:
            raise ValueError("Problem path is not set. Provide a path or set Problem.path before analysis.")
        raise NotImplementedError("this function is not available for the selected backend")

    def restart_analysis(self, *args, **kwargs):
        """Continue a previous analysis from a given increement with additional
        steps.

        Parameters
        ----------
        problem : :class:`compas_fea2.problme.Problem`
            The problem (already analysed) to continue.
        start : float
            Time-step increment.
        steps : [:class:`compas_fea2.problem.Step`]
            List of steps to add to the orignal problem.

        Raises
        ------
        ValueError
            _description_

        Notes
        -----
        For abaqus, you have to specify to save specific files during the original
        analysis by passing the `restart=True` option.

        """
        raise NotImplementedError("this function is not available for the selected backend")

    # =========================================================================
    #                         Results methods - general
    # =========================================================================

    # =========================================================================
    #                         Results methods - displacements
    # =========================================================================
