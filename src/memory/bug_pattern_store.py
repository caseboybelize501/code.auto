import json

class BugPatternStore:
    def __init__(self):
        self.patterns = []
        
    def add_pattern(self, bug_type, language, framework, fix):
        pattern = {
            "bug_type": bug_type,
            "language": language,
            "framework": framework,
            "fix": fix
        }
        self.patterns.append(pattern)
        
    def get_patterns(self):
        return self.patterns
