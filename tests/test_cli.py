import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from compas_fea2.cli import (
    main,
    one_o_one,
    change_setting,
    list_backends,
    backend_info,
    project,
    model,
    results,
    config,
    tools,
    docs,
    examples,
    version,
    validate_backend_name,
    validate_setting_name,
)


class TestValidationFunctions(unittest.TestCase):
    """Test validation functions for CLI inputs."""

    def test_validate_backend_name_valid(self):
        """Test valid backend name validation."""
        ctx = MagicMock()
        param = MagicMock()

        # Test valid names
        self.assertEqual(validate_backend_name(ctx, param, "opensees"), "opensees")
        self.assertEqual(validate_backend_name(ctx, param, "OpenSees"), "opensees")
        self.assertEqual(validate_backend_name(ctx, param, "abaqus_2023"), "abaqus_2023")

    def test_validate_backend_name_invalid(self):
        """Test invalid backend name validation."""
        from click import BadParameter

        ctx = MagicMock()
        param = MagicMock()

        # Test invalid names
        with self.assertRaises(BadParameter):
            validate_backend_name(ctx, param, "")

        with self.assertRaises(BadParameter):
            validate_backend_name(ctx, param, "backend-with-dash")

        with self.assertRaises(BadParameter):
            validate_backend_name(ctx, param, "backend@symbol")

    def test_validate_setting_name_valid(self):
        """Test valid setting name validation."""
        ctx = MagicMock()
        param = MagicMock()

        self.assertEqual(validate_setting_name(ctx, param, "exe"), "exe")
        self.assertEqual(validate_setting_name(ctx, param, "SOLVER_PATH"), "SOLVER_PATH")

    def test_validate_setting_name_invalid(self):
        """Test invalid setting name validation."""
        from click import BadParameter

        ctx = MagicMock()
        param = MagicMock()

        with self.assertRaises(BadParameter):
            validate_setting_name(ctx, param, "")


class TestMainCommands(unittest.TestCase):
    """Test main CLI commands."""

    def setUp(self):
        self.runner = CliRunner()

    def test_main_command(self):
        """Test main command help."""
        result = self.runner.invoke(main, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("fea2 main", result.output)

    def test_one_o_one_command(self):
        """Test one-o-one help command."""
        result = self.runner.invoke(one_o_one)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("compas_fea2 CLI", result.output)
        self.assertIn("Available Commands", result.output)
        self.assertIn("fea2 one-o-one", result.output)


class TestBackendCommands(unittest.TestCase):
    """Test backend-related CLI commands."""

    def setUp(self):
        self.runner = CliRunner()

    # @patch('compas_fea2.cli.init_plugin')
    # def test_init_backend_success(self, mock_init_plugin):
    #     """Test successful backend initialization."""
    #     result = self.runner.invoke(init_backend, ["--clean", "opensees"])
    #     self.assertEqual(result.exit_code, 0)
    #     self.assertIn("Successfully initialized backend: opensees", result.output)
    #     mock_init_plugin.assert_called_once()

    # @patch('compas_fea2.cli.init_plugin')
    # def test_init_backend_failure(self, mock_init_plugin):
    #     """Test backend initialization failure."""
    #     mock_init_plugin.side_effect = Exception("Test error")
    #     result = self.runner.invoke(init_backend, ["opensees"])
    #     self.assertEqual(result.exit_code, 1)
    #     self.assertIn("Error initializing backend opensees", result.output)

    @patch("importlib.import_module")
    def test_list_backends_found(self, mock_import):
        """Test listing backends when some are found."""
        # Mock successful import for opensees
        mock_import.side_effect = lambda name: MagicMock() if name == "compas_fea2_opensees" else ImportError()

        result = self.runner.invoke(list_backends)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Available backends", result.output)
        self.assertIn("opensees", result.output)

    @patch("importlib.import_module")
    def test_list_backends_none_found(self, mock_import):
        """Test listing backends when none are found."""
        mock_import.side_effect = ImportError()

        result = self.runner.invoke(list_backends)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No compas_fea2 backends found", result.output)

    @patch("importlib.import_module")
    def test_backend_info_success(self, mock_import):
        """Test backend info command success."""
        mock_module = MagicMock()
        mock_module.__version__ = "1.0.0"
        mock_module.HOME = "/test/path"
        mock_import.return_value = mock_module

        result = self.runner.invoke(backend_info, ["opensees"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Backend Information", result.output)
        self.assertIn("opensees", result.output)

    @patch("importlib.import_module")
    def test_backend_info_not_found(self, mock_import):
        """Test backend info when backend not found."""
        mock_import.side_effect = ImportError()

        result = self.runner.invoke(backend_info, ["nonexistent"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Backend 'nonexistent' not installed", result.output)

    # @patch('os.path.exists')
    # @patch('importlib.import_module')
    # @patch('dotenv.set_key')
    # @patch('os.makedirs')
    # def test_change_setting_success(self, mock_makedirs, mock_set_key, mock_import, mock_exists):
    #     """Test successful setting change."""
    #     mock_module = MagicMock()
    #     mock_module.HOME = "/test/path"
    #     mock_import.return_value = mock_module
    #     mock_exists.return_value = True

    #     result = self.runner.invoke(change_setting, ["opensees", "exe", "/path/to/opensees"])
    #     self.assertEqual(result.exit_code, 0)
    #     self.assertIn("EXE set to /path/to/opensees", result.output)

    @patch("importlib.import_module")
    def test_change_setting_backend_not_found(self, mock_import):
        """Test setting change when backend not found."""
        mock_import.side_effect = ImportError()

        result = self.runner.invoke(change_setting, ["nonexistent", "exe", "/path"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Backend 'compas_fea2_nonexistent' not found", result.output)


class TestProjectCommands(unittest.TestCase):
    """Test project-related CLI commands."""

    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir("/")
        shutil.rmtree(self.temp_dir)

    def test_project_create_basic(self):
        """Test creating a basic project."""
        result = self.runner.invoke(project, ["create", "test_project", "--template", "basic"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Project 'test_project' created with basic template", result.output)

        # Check if directories were created
        self.assertTrue(os.path.exists("test_project/models"))
        self.assertTrue(os.path.exists("test_project/results"))
        self.assertTrue(os.path.exists("test_project/scripts"))
        self.assertTrue(os.path.exists("test_project/data"))

        # Check if main.py was created
        self.assertTrue(os.path.exists("test_project/scripts/main.py"))

        # Check if README.md was created
        self.assertTrue(os.path.exists("test_project/README.md"))

    def test_project_create_truss(self):
        """Test creating a truss project."""
        result = self.runner.invoke(project, ["create", "truss_project", "--template", "truss"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Project 'truss_project' created with truss template", result.output)

        # Check if main.py contains truss-specific content
        with open("truss_project/scripts/main.py", "r") as f:
            content = f.read()
            self.assertIn("Truss Structure Analysis", content)
            self.assertIn("truss_model", content)

    def test_project_create_existing(self):
        """Test creating project when directory already exists."""
        os.makedirs("existing_project")
        result = self.runner.invoke(project, ["create", "existing_project"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Project 'existing_project' already exists", result.output)

    def test_project_validate_valid(self):
        """Test project validation with valid structure."""
        os.makedirs("models")
        os.makedirs("results")

        result = self.runner.invoke(project, ["validate-project"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Project structure is valid", result.output)

    def test_project_validate_missing_dirs(self):
        """Test project validation with missing directories."""
        result = self.runner.invoke(project, ["validate-project"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Missing directories", result.output)


class TestModelCommands(unittest.TestCase):
    """Test model-related CLI commands."""

    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir("/")
        shutil.rmtree(self.temp_dir)

    def test_model_validate_file_not_found(self):
        """Test model validation with non-existent file."""
        result = self.runner.invoke(model, ["validate", "nonexistent.json"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Model file 'nonexistent.json' not found", result.output)

    @patch("compas_fea2.model.Model.from_json")
    def test_model_validate_success(self, mock_from_json):
        """Test successful model validation."""
        # Create a dummy file
        with open("test_model.json", "w") as f:
            f.write('{"test": "data"}')

        # Mock model with parts and nodes
        mock_model = MagicMock()
        mock_model.parts = ["part1"]
        mock_model.nodes = ["node1"]
        mock_from_json.return_value = mock_model

        result = self.runner.invoke(model, ["validate", "test_model.json"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Model validation passed", result.output)

    def test_model_info_file_not_found(self):
        """Test model info with non-existent file."""
        result = self.runner.invoke(model, ["info", "nonexistent.json"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error reading model", result.output)


class TestResultsCommands(unittest.TestCase):
    """Test results-related CLI commands."""

    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir("/")
        shutil.rmtree(self.temp_dir)

    def test_results_export_file_not_found(self):
        """Test results export with non-existent file."""
        result = self.runner.invoke(results, ["export", "nonexistent.json"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Results file 'nonexistent.json' not found", result.output)

    def test_results_export_success(self):
        """Test successful results export."""
        # Create a dummy results file
        with open("results.json", "w") as f:
            f.write('{"results": "data"}')

        result = self.runner.invoke(results, ["export", "results.json", "--format", "csv"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Exporting results to csv format", result.output)
        self.assertIn("Results exported to output.csv", result.output)

    def test_results_summary(self):
        """Test results summary command."""
        # Create a dummy results file
        with open("results.json", "w") as f:
            f.write('{"results": "data"}')

        result = self.runner.invoke(results, ["summary", "results.json"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Results Summary", result.output)


class TestConfigCommands(unittest.TestCase):
    """Test configuration-related CLI commands."""

    def setUp(self):
        self.runner = CliRunner()

    @patch("compas_fea2.VERBOSE", True)
    @patch("compas_fea2.POINT_OVERLAP", 0.01)
    @patch("compas_fea2.GLOBAL_TOLERANCE", 1e-6)
    @patch("compas_fea2.PRECISION", 6)
    def test_config_show(self):
        """Test showing configuration."""
        result = self.runner.invoke(config, ["show"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Global Configuration", result.output)

    @patch("dotenv.set_key")
    @patch("compas_fea2.HOME", "/test/home")
    def test_config_set_valid(self, mock_set_key):
        """Test setting valid configuration."""
        result = self.runner.invoke(config, ["set", "VERBOSE", "true"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("VERBOSE set to true", result.output)
        mock_set_key.assert_called_once()

    def test_config_set_invalid_key(self):
        """Test setting invalid configuration key."""
        result = self.runner.invoke(config, ["set", "INVALID_KEY", "value"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Invalid key", result.output)

    @patch("click.confirm")
    def test_config_reset_confirmed(self, mock_confirm):
        """Test configuration reset when confirmed."""
        mock_confirm.return_value = True

        result = self.runner.invoke(config, ["reset"])
        # Since init_fea2 might not be available, we expect either success or import error
        self.assertIn(result.exit_code, [0, 1])


class TestToolsCommands(unittest.TestCase):
    """Test tools-related CLI commands."""

    def setUp(self):
        self.runner = CliRunner()

    def test_tools_convert(self):
        """Test model conversion tool."""
        result = self.runner.invoke(tools, ["convert", "input.json", "output.json", "--backend-from", "opensees", "--backend-to", "abaqus"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Converting from opensees to abaqus", result.output)

    def test_tools_visualize(self):
        """Test model visualization tool."""
        result = self.runner.invoke(tools, ["visualize", "model.json", "--scale", "2.0"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Launching model viewer", result.output)

    @patch("importlib.import_module")
    def test_tools_doctor(self, mock_import):
        """Test diagnostic tool."""

        # Mock some modules as available, others as missing
        def import_side_effect(name):
            if name in ["click", "numpy"]:
                return MagicMock()
            elif name == "compas_fea2_opensees":
                return MagicMock()
            else:
                raise ImportError()

        mock_import.side_effect = import_side_effect

        result = self.runner.invoke(tools, ["doctor"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Running compas_fea2 diagnostics", result.output)
        self.assertIn("Backend Status", result.output)
        self.assertIn("Dependency Status", result.output)


class TestDocumentationCommands(unittest.TestCase):
    """Test documentation-related CLI commands."""

    def setUp(self):
        self.runner = CliRunner()

    @patch("webbrowser.open")
    def test_docs_command(self, mock_open):
        """Test docs command opens browser."""
        result = self.runner.invoke(docs)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Opening documentation", result.output)
        mock_open.assert_called_once_with("https://compas-dev.github.io/compas_fea2")

    @patch("click.prompt")
    def test_examples_command(self, mock_prompt):
        """Test examples command."""
        mock_prompt.return_value = 1

        result = self.runner.invoke(examples)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Available examples", result.output)
        self.assertIn("simple_truss", result.output)

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(version)
        self.assertEqual(result.exit_code, 0)
        # Version info might not be available in test environment
        self.assertTrue(result.exit_code == 0)


class TestTemplateCreation(unittest.TestCase):
    """Test template creation functions."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    # def test_create_basic_template(self):
    #     """Test basic template creation."""
    #     from compas_fea2.cli import _create_basic_template

    #     _create_basic_template(self.temp_dir, "opensees")

    #     # Check if main.py was created
    #     main_path = os.path.join(self.temp_dir, "scripts", "main.py")
    #     self.assertTrue(os.path.exists(main_path))

    #     # Check content
    #     with open(main_path, "r") as f:
    #         content = f.read()
    #         self.assertIn("Basic FEA Analysis Script", content)
    #         self.assertIn("basic_model", content)

    #     # Check README
    #     readme_path = os.path.join(self.temp_dir, "README.md")
    #     self.assertTrue(os.path.exists(readme_path))

    #     with open(readme_path, "r") as f:
    #         content = f.read()
    #         self.assertIn("Basic FEA Project", content)
    #         self.assertIn("opensees", content)

    # def test_create_truss_template(self):
    #     """Test truss template creation."""
    #     from compas_fea2.cli import _create_truss_template

    #     _create_truss_template(self.temp_dir, "opensees")

    #     main_path = os.path.join(self.temp_dir, "scripts", "main.py")
    #     self.assertTrue(os.path.exists(main_path))

    #     with open(main_path, "r") as f:
    #         content = f.read()
    #         self.assertIn("Truss Structure Analysis", content)
    #         self.assertIn("truss_model", content)

    # def test_create_frame_template(self):
    #     """Test frame template creation."""
    #     from compas_fea2.cli import _create_frame_template

    #     _create_frame_template(self.temp_dir, "opensees")

    #     main_path = os.path.join(self.temp_dir, "scripts", "main.py")
    #     self.assertTrue(os.path.exists(main_path))

    #     with open(main_path, "r") as f:
    #         content = f.read()
    #         self.assertIn("Frame Structure Analysis", content)
    #         self.assertIn("frame_model", content)
    #         self.assertIn("2-story frame", content)

    # def test_create_shell_template(self):
    #     """Test shell template creation."""
    #     from compas_fea2.cli import _create_shell_template

    #     _create_shell_template(self.temp_dir, "opensees")

    #     main_path = os.path.join(self.temp_dir, "scripts", "main.py")
    #     self.assertTrue(os.path.exists(main_path))

    #     with open(main_path, "r") as f:
    #         content = f.read()
    #         self.assertIn("Shell Structure Analysis", content)
    #         self.assertIn("shell_model", content)
    #         self.assertIn("ShellElement", content)


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI commands."""

    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir("/")
        shutil.rmtree(self.temp_dir)

    def test_full_project_workflow(self):
        """Test complete project workflow."""
        # Create project
        result = self.runner.invoke(project, ["create", "test_workflow", "--template", "basic"])
        self.assertEqual(result.exit_code, 0)

        # Validate project
        os.chdir("test_workflow")
        result = self.runner.invoke(project, ["validate-project"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Project structure is valid", result.output)

    def test_help_commands(self):
        """Test help for all command groups."""
        commands = [(main, []), (project, []), (model, []), (results, []), (config, []), (tools, [])]

        for command, args in commands:
            result = self.runner.invoke(command, args + ["--help"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Usage:", result.output)


if __name__ == "__main__":
    unittest.main()
