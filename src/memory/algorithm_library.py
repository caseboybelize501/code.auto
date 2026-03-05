import json

class AlgorithmLibrary:
    def __init__(self):
        self.algorithms = []
        
    def add_algorithm(self, algorithm, complexity, performance):
        algo = {
            "algorithm": algorithm,
            "complexity": complexity,
            "performance": performance
        }
        self.algorithms.append(algo)
        
    def get_algorithm(self, algorithm):
        for algo in self.algorithms:
            if algo["algorithm"] == algorithm:
                return algo
        return None
