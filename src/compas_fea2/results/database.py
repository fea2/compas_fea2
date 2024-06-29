from sqlalchemy import MetaData, Table, and_, asc, desc, create_engine, select, String
from sqlalchemy.engine import Engine
from sqlalchemy.sql import Select
from typing import List, Dict, Set, Any, Tuple, Iterable

class ResultsDatabase:
    """SQLAlchemy wrapper class to access the SQLite database."""

    def __init__(self, db_uri: str):
        """
        Initialize ResultsDatabase with the database URI.

        Parameters
        ----------
        db_uri : str
            The database URI.
        """
        self.db_uri = "sqlite:///" + db_uri
        self.engine, self.metadata = self.db_connection()
        self.metadata.reflect(bind=self.engine)
        self.tables_classes = {
            "U": DisplacementResultsTable,
            "RF": ReactionResultsTable,
            "C": ContactResultsTable,
            "S": StressResultsTable,
        }


    @property
    def table_names(self) -> List[str]:
        """Return a list of all table names in the database."""
        try:
            return list(self.metadata.tables.keys())
        except Exception as e:
            print(f"Error fetching table names: {e}")
            raise

    @property
    def fields(self) -> List[str]:
        """Return a list of all field names in the database, excluding the 'fields' table if it exists."""
        try:
            return [name for name in self.table_names if name != "fields"]
        except Exception as e:
            print(f"Error fetching fields: {e}")
            raise

    @property
    def tables(self) -> Dict[str, Table]:
        """Return a dictionary of table names to Table objects."""
        try:
            return {table_name: self.get_table_from_name(table_name) for table_name in self.table_names}
        except Exception as e:
            print(f"Error fetching tables: {e}")
            raise

    def db_connection(self) -> Tuple[Engine, MetaData]:
        """
        Create and return a connection to the SQLite database along with its metadata.

        Returns
        -------
        Tuple[Engine, MetaData]
            The SQLAlchemy engine instance and the MetaData instance for the database.
        """
        try:
            engine = create_engine(self.db_uri, pool_pre_ping=True)
            metadata = MetaData()
            return engine, metadata
        except Exception as e:
            print(f"Error creating database connection: {e}")
            raise

    def execute_query(self, query: Select, chunk_size: int = 1000) -> Iterable[Dict[str, Any]]:
        """
        Execute a previously-defined query and fetch results in chunks.

        Parameters
        ----------
        query : Select
            The SQLAlchemy Select object representing the query.
        chunk_size : int, optional
            The number of rows to fetch per chunk (default is 1000).

        Returns
        -------
        Iterable[Dict[str, Any]]
            The result set of the executed query as an iterable of dictionaries.
        """
        try:
            with self.engine.connect() as connection:
                result_proxy = connection.execution_options(stream_results=True).execute(query)
                while True:
                    chunk = result_proxy.fetchmany(chunk_size)
                    if not chunk:
                        break
                    for row in chunk:
                        yield dict(row)
        except Exception as e:
            print(f"Error executing query: {e}")
            raise

    def get_table_from_name(self, table_name: str) -> Table:
        """
        Get a table from the database.

        Parameters
        ----------
        table_name : str
            The name of the table.

        Returns
        -------
        Table
            The table from the database.
        """
        try:
            if table_name not in self.tables_classes:
                raise ValueError(f"Table {table_name} not found in database")
            cls = self.tables_classes.get(table_name)
            table = cls(metadata=self.metadata)
            table._registration = self
            return table
        except Exception as e:
            print(f"Error loading table {table_name}: {e}")
            raise

    def get_column_values(self, table_name: str, column_name: str) -> List[Any]:
        """
        Get all the values in a specific column of a table.

        Parameters
        ----------
        table_name : str
            The name of the table.
        column_name : str
            The name of the column.

        Returns
        -------
        List[Any]
            The list of values in the specified column.
        """
        try:
            table = self.get_table_from_name(table_name)._table
            query = select([table.c[column_name]])
            return [row[column_name] for row in self.execute_query(query)]
        except Exception as e:
            print(f"Error fetching column values from {table_name}.{column_name}: {e}")
            raise



class ResultsTable:
    """Base class for results tables in the database."""

    def __init__(self, table_name, metadata, **kw):
        """
        Initialize a ResultsTable.

        Parameters
        ----------
        table_name : str
            The name of the table.
        metadata : MetaData
            The MetaData instance for the database.
        """
        self._table_name = table_name
        self._table = metadata.tables[table_name]
        self._basic_components = ["step", "part", "key"]
        self._components_names = None
        self._invariants_names = None
        self._results_class = None
        self._results_func = None

    @property
    def db(self):
        """Return the database registration object."""
        return self._registration

    @property
    def all_columns(self) -> List[str]:
        """Return a list of all columns in the table."""
        return self._basic_components + self.all_components

    @property
    def all_components(self) -> List[str]:
        """Return a list of all component names in the table."""
        return self._components_names + self._invariants_names

    @property
    def column_names(self) -> List[str]:
        """Return a list of all column names in the table."""
        try:
            return [column.name for column in self._table.columns]
        except Exception as e:
            print(f"Error fetching column names for table {self._table_name}: {e}")
            raise

    def get_columns_values(self) -> Dict[str, List[Any]]:
        """
        Get all the values in a list of columns of a table.

        Returns
        -------
        Dict[str, List[Any]]
            Dictionary of column names and their corresponding values.
        """
        try:
            return {column_name: self.get_column_values(column_name) for column_name in self.all_columns}
        except Exception as e:
            print(f"Error fetching column values from {self._table_name}: {e}")
            raise

    def get_column_values(self, column_name: str) -> List[Any]:
        """
        Get all the values in a specific column of a table.

        Parameters
        ----------
        column_name : str
            The name of the column.

        Returns
        -------
        List[Any]
            The list of values in the specified column.
        """
        try:
            query = select(self._table.c[column_name])
            return [row[column_name] for row in self.db.execute_query(query)]
        except Exception as e:
            print(f"Error fetching column values from {self._table_name}.{column_name}: {e}")
            raise

    def get_column_unique_values(self, column_name: str) -> Set[Any]:
        """
        Get all unique values in a specific column of a table.

        Parameters
        ----------
        column_name : str
            The name of the column.

        Returns
        -------
        Set[Any]
            The set of unique values in the specified column.
        """
        try:
            return set(self.get_column_values(column_name))
        except Exception as e:
            print(f"Error fetching unique column values from {self._table_name}.{column_name}: {e}")
            raise

    def get_rows(self, columns_names: List[str], filters: Dict[str, List[Any]] = None) -> List[Dict[str, Any]]:
        """
        Get all rows in a table that match the filtering criteria.

        Parameters
        ----------
        columns_names : list
            List of column names to retrieve.
        filters : dict, optional
            Filtering criteria as {"column_name": [admissible values]}.

        Returns
        -------
        List[Dict[str, Any]]
            List of rows as dictionaries of column values.
        """
        try:
            table = self._table
            conditions = []
            if filters:
                for col, values in filters.items():
                    column = table.columns[col]
                    for value in values:
                        if isinstance(column.type, String):
                            conditions.append(column.ilike(f'%{value}%'))
                        else:
                            conditions.append(column == value)
            query = select([table.columns[c] for c in columns_names])
            if conditions:
                query = query.where(and_(*conditions))
            return [dict(row) for row in self.db.execute_query(query)]
        except Exception as e:
            print(f"Error fetching rows from {self._table_name} with filters {filters}: {e}")
            raise

    def get_func_row(self, column_name: str, func: str, filters: Dict[str, List[Any]] = None, columns_names: List[str] = None) -> Dict[str, Any]:
        """
        Get rows in a table that match the filtering criteria and apply a function to them.

        Currently supported functions: "MIN", "MAX".

        Parameters
        ----------
        column_name : str
            The name of the column on which to apply the function.
        func : str
            The function to apply ("MIN" or "MAX").
        filters : dict, optional
            Filtering criteria as {"column_name": [admissible values]}.
        columns_names : list, optional
            List of column names to retrieve.

        Returns
        -------
        Dict[str, Any]
            The result set after applying the function.
        """
        try:
            sql_func = {"MIN": asc, "MAX": desc}
            if func not in sql_func:
                raise ValueError(f"Function {func} not supported")
            table = self._table
            conditions = []
            if filters:
                for col, values in filters.items():
                    column = table.columns[col]
                    for value in values:
                        if isinstance(column.type, String):
                            conditions.append(column.ilike(f'%{value}%'))
                        else:
                            conditions.append(column == value)
            query = select([table.columns[c] for c in columns_names])
            if conditions:
                query = query.where(and_(*conditions))
            query = query.order_by(sql_func[func](table.c[column_name])).limit(1)
            result = next(self.db.execute_query(query), None)
            if result is None:
                raise ValueError(f"No {func} value found for {column_name}")
            return result
        except Exception as e:
            print(f"Error fetching row with {func} from {self._table_name}.{column_name} with filters {filters}: {e}")
            raise

    def get_max_component(self, component: str, filters: Dict[str, Any] = None) -> Any:
        """
        Get the maximum value of a component with given filters.

        Parameters
        ----------
        component : str
            The name of the component.
        filters : dict, optional
            The filtering criteria.

        Returns
        -------
        Any
            The maximum value of the component.
        """
        result = self.get_func_row(component, "MAX", filters, self.all_columns)
        return result[component]

    def get_min_component(self, component: str, filters: Dict[str, Any] = None) -> Any:
        """
        Get the minimum value of a component with given filters.

        Parameters
        ----------
        component : str
            The name of the component.
        filters : dict, optional
            The filtering criteria.

        Returns
        -------
        Any
            The minimum value of the component.
        """
        result = self.get_func_row(component, "MIN", filters, self.all_columns)
        return result[component]

    def get_limits_component(self, component: str, filters: Dict[str, Any] = None) -> List[Any]:
        """
        Get the limits (min and max) of a component for given filters.

        Parameters
        ----------
        component : str
            The name of the component.
        filters : dict, optional
            The filtering criteria.

        Returns
        -------
        List[Any]
            The list containing min and max values of the component.
        """
        return [self.get_min_component(component, filters), self.get_max_component(component, filters)]

    def get_limits_absolute(self, filters: Dict[str, Any] = None) -> List[Any]:
        """
        Get the absolute limits (min and max) of magnitudes with given filters.

        Parameters
        ----------
        filters : dict, optional
            The filtering criteria.

        Returns
        -------
        List[Any]
            The list containing min and max magnitudes.
        """
        limits = []
        for func in ["MIN", "MAX"]:
            result = self.get_func_row("magnitude", func, filters, self.all_columns)
            limits.append(result["magnitude"])
        return limits


class StressResultsTable(ResultsTable):
    """Class representing a stress results table in the database."""

    def __init__(self, metadata):
        super().__init__("S", metadata)
        self._components_names = ["S11", "S22", "S33", "S12", "S13", "S23"]
        self._invariants_names = ["magnitude"]


class StrainResultsTable(ResultsTable):
    """Class representing a strain results table in the database."""

    def __init__(self, metadata):
        super().__init__("E", metadata)
        self._components_names = ["E11", "E22", "E33", "E12", "E13", "E23"]
        self._invariants_names = ["magnitude"]


class ReactionResultsTable(ResultsTable):
    """Class representing a reaction results table in the database."""

    def __init__(self, metadata):
        super().__init__("RF", metadata)
        self._components_names = ["RF1", "RF2", "RF3"]
        self._invariants_names = ["magnitude"]



class ContactResultsTable(ResultsTable):
    """Class representing a contact results table in the database."""

    def __init__(self, metadata):
        super().__init__("C", metadata)


class DisplacementResultsTable(ResultsTable):
    """Class representing a displacement results table in the database."""

    def __init__(self, metadata):
        super().__init__("U", metadata)
        self._components_names = ["U1", "U2", "U3"]
        self._invariants_names = ["magnitude"]

