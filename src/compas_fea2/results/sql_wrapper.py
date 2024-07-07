import sqlalchemy as db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Table, MetaData, Column, String, Float, Integer

def create_connection(db_file=None):
    """Create a database connection to the SQLite database specified by db_file.

    Parameters
    ----------
    db_file : str, optional
        Path to the .db file, by default 'None'. If not provided, the database
        is run in memory.

    Returns
    -------
    engine, connection, metadata
        SQLAlchemy engine, connection, and metadata
    """
    engine = db.create_engine(f"sqlite:///{db_file or ':memory:'}")
    connection = engine.connect()
    metadata = db.MetaData()
    return engine, connection, metadata


def _execute_sql(connection, sql):
    """Execute a SQL statement.

    Parameters
    ----------
    connection : sqlalchemy.engine.base.Connection
        Connection to the database.
    sql : str
        A SQL statement

    Returns
    -------
    None
    """
    try:
        connection.execute(sql)
    except SQLAlchemyError as e:
        print(e)


def create_table(connection, table_name, columns):
    """Create a table with the specified columns.

    Parameters
    ----------
    connection : sqlalchemy.engine.base.Connection
        Connection to the database.
    table_name : str
        Name of the table.
    columns : list of sqlalchemy Column objects
        List of columns to include in the table.

    Returns
    -------
    None
    """
    metadata = db.MetaData()
    table = db.Table(table_name, metadata, *columns)
    try:
        metadata.create_all(connection)
    except SQLAlchemyError as e:
        print(e)


def insert_entry(connection, table, values):
    """Insert an entry into a table.

    Parameters
    ----------
    connection : sqlalchemy.engine.base.Connection
        Connection to the database.
    table : sqlalchemy.Table
        The table to insert into.
    values : dict
        A dictionary of values to insert.

    Returns
    -------
    int
        ID of the inserted row.
    """
    try:
        insert_stmt = table.insert().values(values)
        result = connection.execute(insert_stmt)
        return result.inserted_primary_key
    except SQLAlchemyError as e:
        print(e)


def create_field_description_table(connection):
    """Create the table containing general results information and field descriptions.

    Parameters
    ----------
    connection : sqlalchemy.engine.base.Connection
        Connection to the database.

    Returns
    -------
    None
    """
    columns = [
        Column('field', String, primary_key=True),
        Column('description', String),
        Column('components', String),
        Column('invariants', String)
    ]
    create_table(connection, 'fields', columns)


def insert_field_description(connection, field, description, components_names, invariants_names):
    """Insert a field description into the fields table.

    Parameters
    ----------
    connection : sqlalchemy.engine.base.Connection
        Connection to the database.
    field : str
        Name of the output field.
    description : str
        Description of the field.
    components_names : str
        Comma-separated names of the field components.
    invariants_names : str
        Comma-separated names of the field invariants.

    Returns
    -------
    int
        ID of the inserted row.
    """
    table = get_database_table(connection, 'fields')
    values = {
        'field': field,
        'description': description,
        'components': components_names,
        'invariants': invariants_names
    }
    return insert_entry(connection, table, values)


def create_field_table(connection, field, components_names):
    """Create the results table for the given field.

    Parameters
    ----------
    connection : sqlalchemy.engine.base.Connection
        Connection to the database.
    field : str
        Name of the output field.
    components_names : list
        List of the field components names.

    Returns
    -------
    None
    """
    columns = [
        Column('step', String),
        Column('part', String),
        Column('type', String),
        Column('position', String),
        Column('key', Integer)
    ] + [Column(c, Float) for c in components_names]
    create_table(connection, field, columns)


def insert_field_results(connection, field, node_results_data):
    """Insert the results of the analysis at a node.

    Parameters
    ----------
    connection : sqlalchemy.engine.base.Connection
        Connection to the database.
    field : str
        Name of the output field.
    node_results_data : list
        List of output field components values.

    Returns
    -------
    int
        ID of the inserted row.
    """
    table = get_database_table(connection, field)
    values = dict(zip([c.name for c in table.columns], node_results_data))
    return insert_entry(connection, table, values)


def get_database_table(connection, table_name):
    """Retrieve a table from the database.

    Parameters
    ----------
    connection : sqlalchemy.engine.base.Connection
        Connection to the database.
    table_name : str
        Name of the table to retrieve.

    Returns
    -------
    sqlalchemy.Table
        The retrieved table.
    """
    metadata = db.MetaData(bind=connection)
    return db.Table(table_name, metadata, autoload_with=connection)


def get_query_results(connection, table, columns, test):
    """Get the filtering query to execute.

    Parameters
    ----------
    connection : sqlalchemy.engine.base.Connection
        Connection to the database.
    table : sqlalchemy.Table
        Table to query.
    columns : list
        List of column names to retrieve.
    test : list
        List of conditions to apply.

    Returns
    -------
    list
        Result set of the query.
    """
    query = db.select([table.c[column] for column in columns]).where(db.and_(*test))
    result_proxy = connection.execute(query)
    return result_proxy.fetchall()


def get_field_labels(connection, field, label):
    """Get the names of the components or invariants of the field

    Parameters
    ----------
    connection : sqlalchemy.engine.base.Connection
        Connection to the database.
    field : str
        Name of the field.
    label : str
        'components' or 'invariants'

    Returns
    -------
    list
        List of labels.
    """
    table = get_database_table(connection, 'fields')
    query = db.select([table.c[label]]).where(table.c.field == field)
    result_proxy = connection.execute(query)
    result_set = result_proxy.fetchone()
    return result_set[0].split(" ")


def get_all_field_results(connection, table):
    components = get_field_labels(connection, str(table), "components")
    invariants = get_field_labels(connection, str(table), "invariants")
    columns = ["part", "position", "key"] + components + invariants
    query = db.select([table.c[column] for column in columns])
    result_proxy = connection.execute(query)
    return result_proxy.fetchall()


def get_field_results(connection, table, test):
    components = get_field_labels(connection, str(table), "components")
    invariants = get_field_labels(connection, str(table), "invariants")
    labels = ["part", "position", "key"] + components + invariants
    results = get_query_results(connection, table, labels, test)
    return labels, results


def parse_results_file(filepath):
    """Parse the results file and return the extracted data."""
    with open(filepath, 'r') as file:
        lines = file.readlines()
        # Take the last analysis step and ignore the timestamp (first value)
        data = [float(i) for i in lines[-1].split(' ')[1:]]
    return data
