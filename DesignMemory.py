


class design_memory:
    def __init__(self):
        self.buffer = []

    def add_design(self, parameters, performance):
        """
        Adds a new design and its performance metrics to the memory buffer.
        :param parameters: Dictionary containing design parameters.
        :param performance: Dictionary containing performance metrics like gain margin, phase margin, etc.
        """
        entry = {
            'parameters': parameters,
            'performance': performance
        }
        self.buffer.append(entry)

    def get_all_designs(self):
        """
        Returns all designs and their performances.
        """
        return self.buffer

    def get_latest_design(self):
        """
        Returns the latest design and its performance.
        """
        if self.buffer:
            return self.buffer[-1]
        return None