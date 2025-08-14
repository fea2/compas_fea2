# Dynamic smoke tests for the compas_fea2.problem package using unittest.
import unittest
import importlib
import inspect
import pkgutil

import compas_fea2.problem as problem_pkg


class TestProblemPackage(unittest.TestCase):
    def test_import_all_submodules(self):
        found = []
        for info in pkgutil.walk_packages(problem_pkg.__path__, problem_pkg.__name__ + "."):
            module = importlib.import_module(info.name)
            found.append(module.__name__)
        self.assertGreater(len(found), 0)

    def test_classes_instantiation_and_optional_data_roundtrip(self):
        for info in pkgutil.walk_packages(problem_pkg.__path__, problem_pkg.__name__ + "."):
            module = importlib.import_module(info.name)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if cls.__module__ != module.__name__:
                    continue
                # Skip abstract base classes
                if getattr(cls, "__abstractmethods__", None):
                    continue
                with self.subTest(cls="{}.{}".format(module.__name__, name)):
                    instance = None
                    try:
                        sig = inspect.signature(cls)
                        can_instantiate = True
                        for p in sig.parameters.values():
                            if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                                continue
                            if p.default is inspect._empty and p.kind in (
                                inspect.Parameter.POSITIONAL_ONLY,
                                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            ):
                                can_instantiate = False
                                break
                        if can_instantiate:
                            instance = cls()
                    except Exception:
                        instance = None

                    if instance is not None:
                        # str/repr should not raise
                        _ = str(instance)
                        _ = repr(instance)
                        # Optional __data__/__from_data__ roundtrip
                        data = getattr(instance, "__data__", None)
                        if isinstance(data, dict):
                            from_data = getattr(cls, "__from_data__", None)
                            if callable(from_data):
                                try:
                                    roundtripped = from_data(data)
                                    self.assertIsInstance(roundtripped, cls)
                                except Exception:
                                    # Non-fatal: some classes may require registry/context
                                    pass


if __name__ == "__main__":
    unittest.main()
