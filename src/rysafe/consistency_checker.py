"""Code pattern validator."""
from pathlib import Path
import ast


class CodePatternComparator:
    """Compares new code against existing patterns."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> dict:
        patterns = {'functions': set(), 'classes': set()}
        for file in self.base_path.rglob('*.py'):
            with file.open() as f:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        patterns['functions'].add(node.name)
                    elif isinstance(node, ast.ClassDef):
                        patterns['classes'].add(node.name)
        return patterns
    
    def check_file(self, file_path: Path) -> list:
        deviations = []
        with file_path.open() as f:
            tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not self._is_snake_case(node.name):
                        deviations.append(
                            f"Function {node.name} violates snake_case"
                        )
                
                elif isinstance(node, ast.ClassDef):
                    if not self._is_pascal_case(node.name):
                        deviations.append(
                            f"Class {node.name} violates PascalCase"
                        )
                    
                    for method in node.body:
                        if (isinstance(method, ast.FunctionDef) and 
                            not self._is_snake_case(method.name)):
                            deviations.append(
                                f"Method {method.name} violates snake_case"
                            )
        return deviations
    
    def _is_snake_case(self, name: str) -> bool:
        return name == name.lower() and '_' in name or name.startswith('_')
    
    def _is_pascal_case(self, name: str) -> bool:
        return name[0].isupper() and '_' not in name