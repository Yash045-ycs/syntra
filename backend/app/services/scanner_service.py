import os
from collections import Counter


class ScannerService:

    IGNORED_DIRECTORIES = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "coverage",
        ".next",
        ".nuxt",
        "target",
        "vendor",
    }

    CODE_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".swift",
        ".kt",
        ".kts",
        ".dart",
        ".sql",
        ".html",
        ".css",
        ".scss",
    }

    LANGUAGE_MAP = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".php": "PHP",
        ".rb": "Ruby",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".kts": "Kotlin",
        ".dart": "Dart",
        ".sql": "SQL",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
    }

    DEPENDENCY_FILES = {
        "requirements.txt",
        "pyproject.toml",
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "go.mod",
        "cargo.toml",
        "cargo.lock",
        "gemfile",
        "composer.json",
        "pubspec.yaml",
    }

    TEST_KEYWORDS = {
        "test",
        "tests",
        "spec",
        "specs",
    }

    ENTRY_POINT_FILES = {
        "main.py",
        "app.py",
        "server.py",
        "index.js",
        "index.ts",
        "main.js",
        "main.ts",
        "main.java",
        "main.cpp",
        "main.go",
        "main.rs",
        "manage.py",
        "application.py",
    }

    @classmethod
    def scan_repository(cls, repository_path: str) -> dict:
        files = []
        total_lines = 0

        language_counter = Counter()
        directory_counter = Counter()

        test_files = []
        entry_points = []
        dependency_files = []

        readme_found = False

        for root, directories, filenames in os.walk(repository_path):

            directories[:] = [
                directory
                for directory in directories
                if directory not in cls.IGNORED_DIRECTORIES
            ]

            for filename in filenames:

                relative_path = os.path.relpath(
                    os.path.join(root, filename),
                    repository_path,
                )

                normalized_path = relative_path.replace("\\", "/")

                lower_filename = filename.lower()

                if lower_filename == "readme.md":
                    readme_found = True

                if lower_filename in {
                    name.lower()
                    for name in cls.DEPENDENCY_FILES
                }:
                    dependency_files.append(normalized_path)

                extension = os.path.splitext(filename)[1].lower()

                if extension not in cls.CODE_EXTENSIONS:
                    continue

                file_path = os.path.join(root, filename)

                try:
                    with open(
                        file_path,
                        "r",
                        encoding="utf-8",
                        errors="ignore",
                    ) as file:
                        lines = file.readlines()

                    line_count = len(lines)
                    total_lines += line_count

                    language = cls.LANGUAGE_MAP.get(
                        extension,
                        extension.lstrip(".").upper(),
                    )

                    language_counter[language] += line_count

                    relative_directory = os.path.dirname(
                        normalized_path
                    )

                    if relative_directory:
                        directory_counter[relative_directory] += 1

                    path_parts = normalized_path.lower().split("/")

                    if (
                        lower_filename.startswith("test_")
                        or lower_filename.endswith("_test.py")
                        or lower_filename.endswith(".test.js")
                        or lower_filename.endswith(".test.ts")
                        or lower_filename.endswith(".spec.js")
                        or lower_filename.endswith(".spec.ts")
                        or any(
                            part in cls.TEST_KEYWORDS
                            for part in path_parts
                        )
                    ):
                        test_files.append(normalized_path)

                    if lower_filename in {
                        name.lower()
                        for name in cls.ENTRY_POINT_FILES
                    }:
                        entry_points.append(normalized_path)

                    files.append(
                        {
                            "path": normalized_path,
                            "extension": extension,
                            "language": language,
                            "lines": line_count,
                        }
                    )

                except (OSError, UnicodeError):
                    continue

        languages = dict(
            sorted(
                language_counter.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

        directories = [
            {
                "path": path,
                "files": count,
            }
            for path, count in sorted(
                directory_counter.items(),
                key=lambda item: item[0],
            )
        ]

        project_type = cls.detect_project_type(
            languages,
            dependency_files,
            files,
        )

        return {
            "total_files": len(files),
            "total_lines": total_lines,
            "languages": languages,
            "project_type": project_type,
            "readme_found": readme_found,
            "dependency_files": dependency_files,
            "entry_points": entry_points,
            "test_files": test_files,
            "directories": directories,
            "files": files,
        }

    @classmethod
    def detect_project_type(
        cls,
        languages: dict,
        dependency_files: list,
        files: list,
    ) -> str:

        dependency_names = {
            os.path.basename(path).lower()
            for path in dependency_files
        }

        extensions = {
            file["extension"]
            for file in files
        }

        if "package.json" in dependency_names:
            if ".tsx" in extensions or ".jsx" in extensions:
                return "JavaScript/TypeScript Web Application"

            return "Node.js Application"

        if (
            "requirements.txt" in dependency_names
            or "pyproject.toml" in dependency_names
        ):
            if ".py" in extensions:
                return "Python Application"

        if "pom.xml" in dependency_names:
            return "Java Maven Project"

        if "go.mod" in dependency_names:
            return "Go Application"

        if "cargo.toml" in dependency_names:
            return "Rust Application"

        if "pubspec.yaml" in dependency_names:
            return "Flutter/Dart Application"

        if ".java" in extensions:
            return "Java Application"

        if ".cpp" in extensions or ".c" in extensions:
            return "C/C++ Project"

        if ".dart" in extensions:
            return "Dart Application"

        if languages:
            return f"{next(iter(languages))} Project"

        return "Unknown Project"