import subprocess
from pathlib import Path


class TestRunnerService:

    @classmethod
    def discover(cls, repository_path: str) -> dict:

        repository = Path(repository_path).resolve()

        if not repository.exists():
            raise ValueError(
                f"Repository does not exist: {repository}"
            )

        checks = [
            cls._detect_python(repository),
            cls._detect_node(repository),
            cls._detect_dart(repository),
            cls._detect_go(repository),
            cls._detect_rust(repository),
            cls._detect_java(repository),
            cls._detect_cpp(repository),
        ]

        for result in checks:
            if result is not None:
                return result

        return {
            "detected": False,
            "language": None,
            "framework": None,
            "command": None,
            "reason": "No supported test framework was confidently detected.",
        }

    @classmethod
    def run(
        cls,
        repository_path: str,
        timeout: int = 120,
    ) -> dict:

        test_info = cls.discover(repository_path)

        if not test_info["detected"]:
            return {
                **test_info,
                "executed": False,
                "passed": None,
                "stdout": "",
                "stderr": "",
                "return_code": None,
            }

        repository = Path(repository_path).resolve()

        try:
            result = subprocess.run(
                test_info["command"],
                cwd=repository,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                shell=True,
            )

            return {
                **test_info,
                "executed": True,
                "passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired as exc:
            return {
                **test_info,
                "executed": True,
                "passed": False,
                "stdout": exc.stdout or "",
                "stderr": "Test execution timed out.",
                "return_code": None,
            }

        except OSError as exc:
            return {
                **test_info,
                "executed": False,
                "passed": False,
                "stdout": "",
                "stderr": str(exc),
                "return_code": None,
            }

    @staticmethod
    @staticmethod
    def _detect_python(repository: Path):

        has_python = (
            (repository / "pyproject.toml").exists()
            or (repository / "pytest.ini").exists()
            or (repository / "setup.cfg").exists()
            or (repository / "requirements.txt").exists()
            or any(repository.glob("*.py"))
        )

        if not has_python:
            return None

        has_pytest_config = (
            (repository / "pytest.ini").exists()
            or (repository / "pyproject.toml").exists()
            or (repository / "setup.cfg").exists()
        )

        has_test_directory = (
            (repository / "tests").exists()
            and (repository / "tests").is_dir()
        )

        has_test_files = (
            any(repository.glob("test_*.py"))
            or any(repository.glob("*_test.py"))
            or (
                has_test_directory
                and any(repository.joinpath("tests").rglob("test_*.py"))
            )
        )

        if has_pytest_config or has_test_directory or has_test_files:
            return {
                "detected": True,
                "language": "Python",
                "framework": "pytest",
                "command": "python -m pytest",
                "reason": "Python test configuration or conventional test files detected.",
            }

        return {
            "detected": False,
            "language": "Python",
            "framework": None,
            "command": None,
            "reason": "Python project detected, but no test framework was confidently identified.",
        }

    @staticmethod
    def _detect_node(repository: Path):

        package_json = repository / "package.json"

        if not package_json.exists():
            return None

        try:
            import json

            data = json.loads(
                package_json.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            return {
                "detected": False,
                "language": "JavaScript/TypeScript",
                "framework": None,
                "command": None,
                "reason": "package.json exists but could not be parsed.",
            }

        scripts = data.get("scripts", {})

        if isinstance(scripts, dict) and "test" in scripts:
            return {
                "detected": True,
                "language": "JavaScript/TypeScript",
                "framework": "npm test",
                "command": "npm test",
                "reason": "A test script exists in package.json.",
            }

        return {
            "detected": False,
            "language": "JavaScript/TypeScript",
            "framework": None,
            "command": None,
            "reason": "package.json exists but no test script was found.",
        }

    @staticmethod
    def _detect_dart(repository: Path):

        pubspec = repository / "pubspec.yaml"

        if not pubspec.exists():
            return None

        if any(repository.rglob("*_test.dart")):
            return {
                "detected": True,
                "language": "Dart",
                "framework": "Dart test",
                "command": "dart test",
                "reason": "Dart test files detected.",
            }

        return {
            "detected": False,
            "language": "Dart",
            "framework": None,
            "command": None,
            "reason": "Dart project detected but no test files were found.",
        }

    @staticmethod
    def _detect_go(repository: Path):

        if not (repository / "go.mod").exists():
            return None

        if any(repository.rglob("*_test.go")):
            return {
                "detected": True,
                "language": "Go",
                "framework": "Go test",
                "command": "go test ./...",
                "reason": "Go test files detected.",
            }

        return {
            "detected": False,
            "language": "Go",
            "framework": None,
            "command": None,
            "reason": "Go project detected but no test files were found.",
        }

    @staticmethod
    def _detect_rust(repository: Path):

        if not (repository / "Cargo.toml").exists():
            return None

        return {
            "detected": True,
            "language": "Rust",
            "framework": "Cargo test",
            "command": "cargo test",
            "reason": "Cargo.toml detected.",
        }

    @staticmethod
    def _detect_java(repository: Path):

        if (repository / "pom.xml").exists():
            return {
                "detected": True,
                "language": "Java",
                "framework": "Maven",
                "command": "mvn test",
                "reason": "Maven project detected.",
            }

        if (
            (repository / "build.gradle").exists()
            or (repository / "build.gradle.kts").exists()
        ):
            return {
                "detected": True,
                "language": "Java/Kotlin",
                "framework": "Gradle",
                "command": "gradlew test",
                "reason": "Gradle project detected.",
            }

        return None

    @staticmethod
    def _detect_cpp(repository: Path):

        if (repository / "CMakeLists.txt").exists():
            return {
                "detected": False,
                "language": "C/C++",
                "framework": None,
                "command": None,
                "reason": "CMake project detected, but no safe generic test command was selected.",
            }

        return None
