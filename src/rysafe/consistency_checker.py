"""Code pattern validator."""

import ast
from pathlib import Path
from typing import Dict, List, Set


class CodePatternComparator:
    """
    Compares new code against existing patterns.

    Attributes:
        base_path (Path): Reference code directory
        patterns (Dict[str, Set[str]]): Extracted patterns
    """

    def __init__(self, base_path: str):
        """
        Initialize with reference codebase.

        Args:
            base_path: Path to reference code
        """
        self.base_path = Path(base_path)
        self.patterns = self._load_patterns()

    def _load_patterns(self) -> Dict[str, Set[str]]:
        """
        Extract naming and pattern conventions from base code.

        Returns:
            Dict[str, Set[str]]: Patterns by file type
        """
        patterns = {"functions": set(), "classes": set()}
        for file in self.base_path.rglob("*.py"):
            try:
                with file.open() as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            patterns["functions"].add(node.name)
                        elif isinstance(node, ast.ClassDef):
                            patterns["classes"].add(node.name)
            except (SyntaxError, UnicodeDecodeError):
                # Skip files with syntax errors or encoding issues
                continue
        return patterns

    def check_file(self, file_path: Path) -> List[str]:
        """
        Validate new file against patterns.

        Args:
            file_path: File to validate

        Returns:
            List[str]: Deviation messages
        """
        deviations = []
        try:
            with file_path.open() as f:
                tree = ast.parse(f.read())
        except (SyntaxError, UnicodeDecodeError) as e:
            return [f"Failed to parse {file_path}: {e}"]

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not self._is_snake_case(node.name):
                    deviations.append(
                        f"Function '{node.name}' violates snake_case"
                    )

            elif isinstance(node, ast.ClassDef):
                if not self._is_pascal_case(node.name):
                    deviations.append(
                        f"Class '{node.name}' violates PascalCase"
                    )

                # Check method consistency
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if not self._is_snake_case(item.name):
                            deviations.append(
                                f"Method '{item.name}' in class '{node.name}' "
                                f"violates snake_case"
                            )

        return deviations

    def _is_snake_case(self, name: str) -> bool:
        """
        Check if name follows snake_case convention.

        Args:
            name: Name to check

        Returns:
            bool: True if valid snake_case
        """
        # Special cases for dunder methods
        if name.startswith("__") and name.endswith("__"):
            return True

        # Private/protected methods can start with underscore(s)
        if name.startswith("_"):
            name = name.lstrip("_")
            if not name:  # Just underscores
                return False

        # Empty name is invalid
        if not name:
            return False

        # Check if all lowercase with optional underscores
        # Valid: hello, hello_world, _private, __private
        # Invalid: helloWorld, HelloWorld, hello-world
        return (
            name.islower()
            and name.replace("_", "").isalnum()
            and not name.startswith("_")  # After stripping leading _
            and not name.endswith("_")
            and "__" not in name  # No double underscores in middle
        )

    def _is_pascal_case(self, name: str) -> bool:
        """
        Check if name follows PascalCase convention.

        Args:
            name: Name to check

        Returns:
            bool: True if valid PascalCase
        """
        # Empty name is invalid
        if not name:
            return False

        # Must start with uppercase
        if not name[0].isupper():
            return False

        # No underscores allowed in PascalCase
        if "_" in name:
            return False

        # Must be alphanumeric
        if not name.isalnum():
            return False

        # Check for at least one lowercase letter (to distinguish from CONSTANTS)
        # Exception: Single letter classes like 'T' for generics
        if len(name) > 1 and name.isupper():
            return False

        return True

    def validate_project(self, project_path: str) -> Dict[str, List[str]]:
        """
        Validate entire project for naming consistency.

        Args:
            project_path: Root path of project

        Returns:
            Dict[str, List[str]]: Deviations by file
        """
        project_root = Path(project_path)
        all_deviations = {}

        for py_file in project_root.rglob("*.py"):
            # Skip __pycache__ and other generated files
            if "__pycache__" in str(py_file):
                continue

            deviations = self.check_file(py_file)
            if deviations:
                all_deviations[str(py_file)] = deviations

        return all_deviations


class NamingConventionValidator:
    """Additional naming convention utilities."""

    @staticmethod
    def is_constant(name: str) -> bool:
        """Check if name follows CONSTANT_CASE convention."""
        return (
            name.isupper()
            and name.replace("_", "").isalnum()
            and not name.startswith("_")
            and not name.endswith("_")
        )

    @staticmethod
    def suggest_name(name: str, target_case: str) -> str:
        """
        Suggest a corrected name in the target case.

        Args:
            name: Current name
            target_case: One of 'snake_case', 'PascalCase', 'CONSTANT_CASE'

        Returns:
            str: Suggested name
        """
        # Remove special characters and split on case boundaries
        import re

        # Split on underscores, hyphens, and case changes
        parts = re.findall(
            r"[A-Z][a-z]+|[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|[0-9]+", name
        )
        parts = [p.lower() for p in parts if p]

        if target_case == "snake_case":
            return "_".join(parts)
        elif target_case == "PascalCase":
            return "".join(p.capitalize() for p in parts)
        elif target_case == "CONSTANT_CASE":
            return "_".join(p.upper() for p in parts)
        else:
            return name
