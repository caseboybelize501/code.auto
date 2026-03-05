import json

class ArchitectureGraph:
    def __init__(self):
        self.graph = {}
        
    def add_pattern(self, pattern, performance, scalability):
        self.graph[pattern] = {
            "performance": performance,
            "scalability": scalability
        }
        
    def get_performance(self, pattern):
        return self.graph.get(pattern, {}).get("performance")
