import json
import os
from collections import Counter


class ScannerService:

    IGNORED_DIRECTORIES = {
        ".git",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "coverage",
        ".next",
        ".nuxt",
        ".output",
        "target",
        "vendor",
        "bin",
        "obj",
        ".gradle",
    }

    LANGUAGE_MAP = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".mjs": "JavaScript",
        ".cjs": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".kt": "Kotlin",
        ".kts": "Kotlin",
        ".scala": "Scala",
        ".groovy": "Groovy",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".hpp": "C++",
        ".h": "C/C++ Header",
        ".c": "C",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".swift": "Swift",
        ".dart": "Dart",
        ".php": "PHP",
        ".rb": "Ruby",
        ".r": "R",
        ".lua": "Lua",
        ".pl": "Perl",
        ".pm": "Perl",
        ".hs": "Haskell",
        ".ex": "Elixir",
        ".exs": "Elixir",
        ".erl": "Erlang",
        ".hrl": "Erlang",
        ".fs": "F#",
        ".fsx": "F#",
        ".sql": "SQL",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sass": "Sass",
        ".less": "LESS",
        ".vue": "Vue",
        ".svelte": "Svelte",
        ".sh": "Shell",
        ".bash": "Shell",
        ".ps1": "PowerShell",
        ".pl": "Perl",
    }

    DEPENDENCY_FILES = {
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "pipfile",
        "poetry.lock",
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "bun.lockb",
        "bun.lock",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
        "go.mod",
        "go.sum",
        "cargo.toml",
        "cargo.lock",
        "gemfile",
        "gemfile.lock",
        "composer.json",
        "pubspec.yaml",
        "mix.exs",
        "mix.lock",
        "cmakelists.txt",
        "makefile",
    }

    CONFIG_FILES = {
        ".env",
        ".env.example",
        ".gitignore",
        "dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "tsconfig.json",
        "jsconfig.json",
        "vite.config.js",
        "vite.config.ts",
        "next.config.js",
        "next.config.ts",
        "nuxt.config.ts",
        "angular.json",
        "webpack.config.js",
        "rollup.config.js",
        "tailwind.config.js",
        "tailwind.config.ts",
        "eslint.config.js",
        ".eslintrc",
        ".eslintrc.json",
        ".prettierrc",
        "pytest.ini",
        "tox.ini",
        "setup.cfg",
        "ruff.toml",
        "mypy.ini",
        "cargo.toml",
        "cmakelists.txt",
        "makefile",
    }

    ENTRY_POINT_FILES = {
        "main.py",
        "app.py",
        "server.py",
        "manage.py",
        "index.js",
        "index.jsx",
        "index.ts",
        "index.tsx",
        "main.js",
        "main.jsx",
        "main.ts",
        "main.tsx",
        "main.py",
        "main.java",
        "main.cpp",
        "main.c",
        "main.go",
        "main.rs",
        "application.py",
        "program.cs",
        "main.dart",
    }

    TEST_FILE_PATTERNS = (
        "test_",
        "_test.",
        ".test.",
        ".spec.",
        "spec_",
    )

    @classmethod
    def scan_repository(
        cls,
        repository_path: str,
    ) -> dict:

        files = []
        total_lines = 0

        language_counter = Counter()
        directory_counter = Counter()

        test_files = []
        entry_points = []
        dependency_files = []
        config_files = []

        readme_found = False

        for root, directories, filenames in os.walk(
            repository_path
        ):

            directories[:] = [
                directory
                for directory in directories
                if directory.lower()
                not in cls.IGNORED_DIRECTORIES
            ]

            for filename in filenames:

                relative_path = os.path.relpath(
                    os.path.join(
                        root,
                        filename,
                    ),
                    repository_path,
                )

                normalized_path = relative_path.replace(
                    "\\",
                    "/",
                )

                lower_filename = filename.lower()

                if lower_filename == "readme.md":
                    readme_found = True

                if (
                    lower_filename
                    in {
                        name.lower()
                        for name in cls.DEPENDENCY_FILES
                    }
                ):
                    dependency_files.append(
                        normalized_path
                    )

                if (
                    lower_filename
                    in {
                        name.lower()
                        for name in cls.CONFIG_FILES
                    }
                ):
                    config_files.append(
                        normalized_path
                    )

                extension = os.path.splitext(
                    filename
                )[1].lower()

                language = cls.LANGUAGE_MAP.get(
                    extension
                )

                if not language:
                    continue

                file_path = os.path.join(
                    root,
                    filename,
                )

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

                    language_counter[
                        language
                    ] += line_count

                    relative_directory = os.path.dirname(
                        normalized_path
                    )

                    if relative_directory:
                        directory_counter[
                            relative_directory
                        ] += 1

                    lower_path = normalized_path.lower()

                    if any(
                        pattern in lower_path
                        for pattern
                        in cls.TEST_FILE_PATTERNS
                    ):

                        test_files.append(
                            normalized_path
                        )

                    if (
                        lower_filename
                        in {
                            name.lower()
                            for name
                            in cls.ENTRY_POINT_FILES
                        }
                    ):

                        entry_points.append(
                            normalized_path
                        )

                    files.append(
                        {
                            "path": normalized_path,
                            "extension": extension,
                            "language": language,
                            "lines": line_count,
                        }
                    )

                except (
                    OSError,
                    UnicodeError,
                ):
                    continue

        languages = dict(
            sorted(
                language_counter.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

        primary_language = (
            next(iter(languages))
            if languages
            else None
        )

        directories = [
            {
                "path": path,
                "files": count,
            }
            for path, count in sorted(
                directory_counter.items()
            )
        ]

        project_type = cls.detect_project_type(
            languages,
            dependency_files,
            files,
        )

        frameworks = cls.detect_frameworks(
            repository_path,
            dependency_files,
        )

        package_managers = cls.detect_package_managers(
            dependency_files
        )

        build_systems = cls.detect_build_systems(
            dependency_files,
            config_files,
        )

        test_frameworks = cls.detect_test_frameworks(
            repository_path,
            dependency_files,
        )

        return {
            "total_files": len(files),
            "total_lines": total_lines,
            "languages": languages,
            "primary_language": primary_language,
            "project_type": project_type,
            "frameworks": frameworks,
            "package_managers": package_managers,
            "build_systems": build_systems,
            "test_frameworks": test_frameworks,
            "readme_found": readme_found,
            "dependency_files": dependency_files,
            "config_files": config_files,
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

            if (
                ".tsx" in extensions
                or ".jsx" in extensions
            ):
                return "JavaScript/TypeScript Web Application"

            if (
                ".vue" in extensions
                or ".svelte" in extensions
            ):
                return "Frontend Web Application"

            if (
                ".ts" in extensions
                or ".js" in extensions
            ):
                return "JavaScript/TypeScript Application"

            return "Node.js Application"

        if (
            "requirements.txt" in dependency_names
            or "pyproject.toml" in dependency_names
            or "setup.py" in dependency_names
            or "pipfile" in dependency_names
        ):

            if ".py" in extensions:
                return "Python Application"

        if "pom.xml" in dependency_names:
            return "Java Maven Project"

        if (
            "build.gradle" in dependency_names
            or "build.gradle.kts" in dependency_names
        ):
            return "Java Gradle Project"

        if "go.mod" in dependency_names:
            return "Go Application"

        if "cargo.toml" in dependency_names:
            return "Rust Application"

        if "pubspec.yaml" in dependency_names:
            return "Flutter/Dart Application"

        if "mix.exs" in dependency_names:
            return "Elixir Application"

        if "composer.json" in dependency_names:
            return "PHP Application"

        if "gemfile" in dependency_names:
            return "Ruby Application"

        if "cmakelists.txt" in dependency_names:
            if ".cpp" in extensions:
                return "C++ Application"

            if ".c" in extensions:
                return "C Application"

            return "C/C++ Project"

        if (
            ".html" in extensions
            or ".htm" in extensions
        ):

            if (
                ".css" in extensions
                or ".scss" in extensions
                or ".sass" in extensions
            ):
                return "HTML/CSS Web Application"

            return "HTML Web Application"

        if (
            ".cpp" in extensions
            or ".cc" in extensions
            or ".cxx" in extensions
        ):
            return "C++ Project"

        if ".c" in extensions:
            return "C Project"

        if ".java" in extensions:
            return "Java Application"

        if ".go" in extensions:
            return "Go Application"

        if ".rs" in extensions:
            return "Rust Application"

        if ".dart" in extensions:
            return "Dart Application"

        if ".swift" in extensions:
            return "Swift Application"

        if ".kt" in extensions:
            return "Kotlin Application"

        if ".php" in extensions:
            return "PHP Application"

        if ".rb" in extensions:
            return "Ruby Application"

        if ".cs" in extensions:
            return "C# Application"

        if languages:
            return f"{next(iter(languages))} Project"

        return "Unknown Project"

    @classmethod
    def detect_frameworks(
        cls,
        repository_path: str,
        dependency_files: list,
    ) -> list:

        frameworks = []

        package_json_path = os.path.join(
            repository_path,
            "package.json",
        )

        if os.path.isfile(package_json_path):

            try:

                with open(
                    package_json_path,
                    "r",
                    encoding="utf-8",
                ) as file:
                    package = json.load(file)

                dependencies = {}

                dependencies.update(
                    package.get(
                        "dependencies",
                        {},
                    )
                )

                dependencies.update(
                    package.get(
                        "devDependencies",
                        {},
                    )
                )

                checks = {
                    "react": "React",
                    "next": "Next.js",
                    "vue": "Vue",
                    "@angular/core": "Angular",
                    "svelte": "Svelte",
                    "express": "Express",
                    "fastify": "Fastify",
                    "nestjs": "NestJS",
                    "@nestjs/core": "NestJS",
                    "vite": "Vite",
                    "electron": "Electron",
                    "react-native": "React Native",
                    "tailwindcss": "Tailwind CSS",
                }

                for package_name, framework in checks.items():

                    if package_name in dependencies:
                        frameworks.append(
                            framework
                        )

            except (
                OSError,
                json.JSONDecodeError,
            ):
                pass

        python_files = {
            os.path.basename(path).lower()
            for path in dependency_files
        }

        if (
            "requirements.txt" in python_files
            or "pyproject.toml" in python_files
        ):

            dependency_text = ""

            for filename in (
                "requirements.txt",
                "pyproject.toml",
            ):

                path = os.path.join(
                    repository_path,
                    filename,
                )

                if os.path.isfile(path):

                    try:

                        with open(
                            path,
                            "r",
                            encoding="utf-8",
                            errors="ignore",
                        ) as file:
                            dependency_text += (
                                file.read().lower()
                            )

                    except OSError:
                        pass

            python_frameworks = {
                "fastapi": "FastAPI",
                "django": "Django",
                "flask": "Flask",
                "streamlit": "Streamlit",
                "tensorflow": "TensorFlow",
                "torch": "PyTorch",
                "scikit-learn": "scikit-learn",
            }

            for package_name, framework in (
                python_frameworks.items()
            ):

                if package_name in dependency_text:
                    frameworks.append(
                        framework
                    )

        return sorted(
            set(frameworks)
        )

    @classmethod
    def detect_package_managers(
        cls,
        dependency_files: list,
    ) -> list:

        names = {
            os.path.basename(path).lower()
            for path in dependency_files
        }

        managers = []

        if (
            "package-lock.json" in names
            or "package.json" in names
        ):
            managers.append("npm")

        if "yarn.lock" in names:
            managers.append("Yarn")

        if (
            "pnpm-lock.yaml" in names
        ):
            managers.append("pnpm")

        if (
            "bun.lockb" in names
            or "bun.lock" in names
        ):
            managers.append("Bun")

        if (
            "requirements.txt" in names
            or "setup.py" in names
            or "setup.cfg" in names
        ):
            managers.append("pip")

        if "pyproject.toml" in names:
            managers.append("Python packaging")

        if (
            "poetry.lock" in names
        ):
            managers.append("Poetry")

        if (
            "pom.xml" in names
        ):
            managers.append("Maven")

        if (
            "build.gradle" in names
            or "build.gradle.kts" in names
        ):
            managers.append("Gradle")

        if "go.mod" in names:
            managers.append("Go Modules")

        if "cargo.toml" in names:
            managers.append("Cargo")

        if "pubspec.yaml" in names:
            managers.append("Pub")

        if "gemfile" in names:
            managers.append("Bundler")

        if "composer.json" in names:
            managers.append("Composer")

        return sorted(
            set(managers)
        )

    @classmethod
    def detect_build_systems(
        cls,
        dependency_files: list,
        config_files: list,
    ) -> list:

        names = {
            os.path.basename(path).lower()
            for path in (
                dependency_files
                + config_files
            )
        }

        systems = []

        if (
            "package.json" in names
        ):
            systems.append("npm")

        if "pom.xml" in names:
            systems.append("Maven")

        if (
            "build.gradle" in names
            or "build.gradle.kts" in names
        ):
            systems.append("Gradle")

        if "cargo.toml" in names:
            systems.append("Cargo")

        if "go.mod" in names:
            systems.append("Go")

        if "cmakelists.txt" in names:
            systems.append("CMake")

        if "makefile" in names:
            systems.append("Make")

        return sorted(
            set(systems)
        )

    @classmethod
    def detect_test_frameworks(
        cls,
        repository_path: str,
        dependency_files: list,
    ) -> list:

        frameworks = []

        names = {
            os.path.basename(path).lower()
            for path in dependency_files
        }

        if (
            "pytest.ini" in names
            or "requirements.txt" in names
            or "pyproject.toml" in names
        ):

            dependency_text = ""

            for filename in (
                "requirements.txt",
                "pyproject.toml",
            ):

                path = os.path.join(
                    repository_path,
                    filename,
                )

                if os.path.isfile(path):

                    try:

                        with open(
                            path,
                            "r",
                            encoding="utf-8",
                            errors="ignore",
                        ) as file:
                            dependency_text += (
                                file.read().lower()
                            )

                    except OSError:
                        pass

            if "pytest" in dependency_text:
                frameworks.append("pytest")

            if "unittest" in dependency_text:
                frameworks.append("unittest")

        package_json_path = os.path.join(
            repository_path,
            "package.json",
        )

        if os.path.isfile(package_json_path):

            try:

                with open(
                    package_json_path,
                    "r",
                    encoding="utf-8",
                ) as file:
                    package = json.load(file)

                dependencies = {}

                dependencies.update(
                    package.get(
                        "dependencies",
                        {},
                    )
                )

                dependencies.update(
                    package.get(
                        "devDependencies",
                        {},
                    )
                )

                checks = {
                    "jest": "Jest",
                    "vitest": "Vitest",
                    "mocha": "Mocha",
                    "jasmine": "Jasmine",
                    "@playwright/test": "Playwright",
                    "cypress": "Cypress",
                }

                for package_name, framework in (
                    checks.items()
                ):

                    if package_name in dependencies:
                        frameworks.append(
                            framework
                        )

            except (
                OSError,
                json.JSONDecodeError,
            ):
                pass

        if "go.mod" in names:
            frameworks.append("Go testing")

        if "cargo.toml" in names:
            frameworks.append("Rust test")

        if "pubspec.yaml" in names:
            frameworks.append("Flutter test")

        return sorted(
            set(frameworks)
        )