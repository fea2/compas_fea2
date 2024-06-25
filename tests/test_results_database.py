# test_results_database.py
from compas_fea2.results import ResultsDatabase

from data.setup_test_db import setup_test_db

import pytest
import os
import tempfile

@pytest.fixture(scope="module")
def db_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_db.sqlite")
        setup_test_db(db_path)
        yield db_path

@pytest.fixture(scope="module")
def results_db(db_path):
    return ResultsDatabase(db_path)

def test_table_names(results_db):
    assert 'U' in results_db.table_names
    assert 'RF' in results_db.table_names

def test_get_column_values(results_db):
    values = results_db.get_column_values('U', 'U1')
    assert values == [0.1, 0.4, 0.7]

def test_get_column_unique_values(results_db):
    unique_values = results_db.tables['U'].get_column_unique_values('step')
    assert unique_values == {'Step1', 'Step2'}

def test_get_rows(results_db):
    filters = {'step': ['Step1']}
    rows = results_db.tables['U'].get_rows(['step', 'part', 'key'], filters)
    assert len(rows) == 2
    assert rows[0]['key'] == 1

def test_get_func_row(results_db):
    filters = {'step': ['Step1']}
    max_row = results_db.tables['U'].get_func_row('U1', 'MAX', filters, ['U1'])
    assert max_row['U1'] == 0.4

def test_get_max_component(results_db):
    max_value = results_db.tables['U'].get_max_component('magnitude')
    assert max_value == 1.204

def test_get_min_component(results_db):
    min_value = results_db.tables['U'].get_min_component('magnitude')
    assert min_value == 0.374

def test_get_limits_component(results_db):
    limits = results_db.tables['U'].get_limits_component('magnitude')
    assert limits == [0.374, 1.204]

def test_get_limits_absolute(results_db):
    limits = results_db.tables['U'].get_limits_absolute()
    assert limits == [0.374, 1.204]
