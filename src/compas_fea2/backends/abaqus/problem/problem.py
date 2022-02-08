from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pathlib import Path
from compas_fea2.problem import Problem

from compas_fea2.backends.abaqus.job import AbaqusInputFile
from compas_fea2.backends.abaqus.job import AbaqusParFile
from compas_fea2.backends.abaqus.job import launch_process
from compas_fea2.backends.abaqus.job import launch_optimisation


class AbaqusProblem(Problem):
    """Initialises the Problem object.

    Parameters
    ----------
    name : str
        Name of the Structure.
    model : obj
        model object.
    parts : list
        List of the parts in the model.

    Attributes
    ----------
    None
    """

    def __init__(self, name, model, **kwargs):
        super(AbaqusProblem, self).__init__(name=name, model=model, **kwargs)
        # self.__name__ = 'AbaqusProblem'
        # self.parts = model.parts.values()  # TODO remove
        # self.interactions       = model.interactions

    # =========================================================================
    #                           Optimisation methods
    # =========================================================================

    # TODO move to the base class and change to **kwargs
    def set_optimisation_parameters(self, vf, iter_max, cpus):
        self.vf = vf
        self.iter_max = iter_max
        self.cpus = cpus

    # =========================================================================
    #                         Analysis methods
    # =========================================================================

    def write_input_file(self, output=True):
        """Writes the abaqus input file.

        Parameters
        ----------
        output : bool
            Print terminal output.

        Returns
        -------
        None
        """
        input_file = AbaqusInputFile(self)
        r = input_file.write_to_file(self.path)
        if output:
            print(r)

    def write_parameters_file(self, output=True):
        """Writes the abaqus parameters file for the optimisation.

        Parameters
        ----------
        output : bool
            Print terminal output.

        Returns
        -------
        None
        """
        par_file = AbaqusParFile(self)
        par = par_file.write_to_file(self.path)
        if output:
            print(par)

    # TODO: try to make this an abstract method of the base class
    def analyse(self, path='C:/temp', exe=None, cpus=1, output=True, overwrite=True, user_mat=False, save=False):
        """Runs the analysis through abaqus.

        Parameters
        ----------
        path : str
            Path to the folder where the input file is saved.
        exe : str
            Full terminal command to bypass subprocess defaults.
        cpus : int
            Number of CPU cores to use.
        output : bool
            Print terminal output.
        user_mat : str TODO: REMOVE!
            Name of the material defined through a subroutine (currently only one material is supported)
        save : bool
            Save structure to .cfp before file writing.

        Returns
        -------
        None

        """
        self.path = path if isinstance(path, Path) else Path(path)
        if not self.path.exists():
            self.path.mkdir()

        if save:
            self.save_to_cfp()

        self.write_input_file(output)
        launch_process(self, exe, output, overwrite, user_mat)

    def optimise(self, path='C:/temp', output=True, save=False):
        self.path = path if isinstance(path, Path) else Path(path)
        if not self.path.exists():
            self.path.mkdir()

        if save:
            self.save_to_cfp()

        self.write_input_file(output)
        self.write_parameters_file(output)
        launch_optimisation(self, output)

    # =============================================================================
    #                               Job data
    # =============================================================================

    def _generate_jobdata(self):
        return f"""**
** STEPS
{self._generate_steps_section()}"""

    def _generate_steps_section(self):
        """Generate the content relatitive to the steps section for the input
        file.

        Parameters
        ----------
        problem : obj
            compas_fea2 Problem object.

        Returns
        -------
        str
            text section for the input file.
        """
        section_data = []
        for step in self.steps.values():
            section_data.append(step._generate_jobdata())

        return ''.join(section_data)


# TODO: add cpu parallelization option. Parallel execution requested but no parallel feature present in the setup

# =========================================================================
#                         Results methods
# =========================================================================

# # TODO: try to make this an abstract method of the base class
# def extract(self, fields='u', steps='all', exe=None, sets=None, license='research', output=True,
#             return_data=True, components=None):
#     """Extracts data from the analysis output files.

#     Parameters
#     ----------
#     fields : list, str
#         Data field requests.
#     steps : list
#         Loads steps to extract from.
#     exe : str
#         Full terminal command to bypass subprocess defaults.
#     sets : list
#         -
#     license : str
#         Software license type: 'research', 'student'.
#     output : bool
#         Print terminal output.
#     return_data : bool
#         Return data back into structure.results.
#     components : list
#         Specific components to extract from the fields data.

#     Returns
#     -------
#     None

#     """
#     extract_data(self, fields=fields, exe=exe, output=output, return_data=return_data,
#                  components=components)

# # this should be an abstract method of the base class
# def analyse_and_extract(self, fields='u', exe=None, cpus=4, license='research', output=True, save=False,
#                         return_data=True, components=None, user_mat=False, overwrite=True):
#     """Runs the analysis through the chosen FEA software / library and extracts data.

#     Parameters
#     ----------
#     fields : list, str
#         Data field requests.
#     exe : str
#         Full terminal command to bypass subprocess defaults.
#     cpus : int
#         Number of CPU cores to use.
#     license : str
#         Software license type: 'research', 'student'.
#     output : bool
#         Print terminal output.
#     save : bool
#         Save the structure to .obj before writing.
#     return_data : bool
#         Return data back into structure.results.
#     components : list
#         Specific components to extract from the fields data.
#     user_sub : bool
#         Specify the user subroutine if needed.
#     delete : bool
#         If True, the analysis results are deleted after being read. [Not Implemented yet]

#     Returns
#     -------
#     None

#     """

#     self.analyse(exe=exe, fields=fields, cpus=cpus, license=license, output=output, user_mat=user_mat,
#                 overwrite=overwrite, save=save)

#     self.extract(fields=fields, exe=exe, license=license, output=output,
#                 return_data=return_data, components=components)

# # this should be stored in a more generic way
# def get_nodal_results(self, step, field, nodes='all'):
#     """Extract nodal results from self.results.

#     Parameters
#     ----------
#     step : str
#         Step to extract from.
#     field : str
#         Data field request.
#     nodes : str, list
#         Extract 'all' or a node set/list.

#     Returns
#     -------
#     dict
#         The nodal results for the requested field.
#     """
#     data  = {}
#     rdict = self.results[step]['nodal']

#     if nodes == 'all':
#         keys = list(self.nodes.keys())
#     elif isinstance(nodes, str):
#         keys = self.sets[nodes].selection
#     else:
#         keys = nodes

#     for key in keys:
#         data[key] = rdict[field][key]

#     return data

# def get_element_results(self, step, field, elements='all'):
#     """Extract element results from self.results.

#     Parameters
#     ----------
#     step : str
#         Step to extract from.
#     field : str
#         Data field request.
#     elements : str, list
#         Extract 'all' or an element set/list.

#     Returns
#     -------
#     dict
#         The element results for the requested field.

#     """
#     data  = {}
#     rdict = self.results[step]['element']

#     if elements == 'all':
#         keys = list(self.elements.keys())
#     elif isinstance(elements, str):
#         keys = self.sets[elements].selection
#     else:
#         keys = elements

#     for key in keys:
#         data[key] = rdict[field][key]

#     return data
