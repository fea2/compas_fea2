class Parser:
    """Parser class for parsing results from a file."""

    def __init__(self, problem):
        """Initialize the parser with a filename."""
        self.problem = problem
        self.data = {}
        self.results = None

    def parse(self):
        raise NotImplementedError("This method should be implemented in the backend.")
    
    

