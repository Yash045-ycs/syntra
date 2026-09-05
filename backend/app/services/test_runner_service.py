import json
import os
import subprocess
import sys


class TestRunnerService:

    @staticmethod
    def read_package_json(
        repository_path: str,
    ) -> dict:

        path = os.path.join(
            repository_path,
            "package.json",
        )

        if not os.path.isfile(path):
            return {}

        try:
            with open(
                path,
                "r",
                encoding="utf-8",
            ) as file:
                return json.load(file)

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

    @staticmethod
    def detect_validation_commands(
        repository_path: str,
        analysis: dict,
    ) -> list:

        project_type = (
            analysis.get("project_type")
            or ""
        ).lower()

        build_systems = {
            item.lower()
            for item in analysis.get(
                "build_systems",
                [],
            )
        }

        test_frameworks = {
            item.lower()
            for item in analysis.get(
                "test_frameworks",
                [],
            )
        }

        commands = []

        package = TestRunnerService.read_package_json(
            repository_path
        )

        scripts = package.get(
            "scripts",
            {},
        )

        if "npm" in build_systems:

            if "test" in scripts:
                commands.append(
                    {
                        "type": "test",
                        "command": [
                            "npm",
                            "test",
                        ],
                    }
                )

            elif "build" in scripts:
                commands.append(
                    {
                        "type": "build",
                        "command": [
                            "npm",
                            "run",
                            "build",
                        ],
                    }
                )

            if "typecheck" in scripts:
                commands.append(
                    {
                        "type": "typecheck",
                        "command": [
                            "npm",
                            "run",
                            "typecheck",
                        ],
                    }
                )

            if "lint" in scripts:
                commands.append(
                    {
                        "type": "lint",
                        "command": [
                            "npm",
                            "run",
                            "lint",
                        ],
                    }
                )

        if "maven" in build_systems:

            commands.append(
                {
                    "type": "test",
                    "command": [
                        "mvn",
                        "test",
                    ],
                }
            )

        if "gradle" in build_systems:

            commands.append(
                {
                    "type": "test",
                    "command": [
                        "gradle",
                        "test",
                    ],
                }
            )

        if "cargo" in build_systems:

            commands.append(
                {
                    "type": "test",
                    "command": [
                        "cargo",
                        "test",
                    ],
                }
            )

            commands.append(
                {
                    "type": "build",
                    "command": [
                        "cargo",
                        "check",
                    ],
                }
            )

        if "go" in build_systems:

            commands.append(
                {
                    "type": "test",
                    "command": [
                        "go",
                        "test",
                        "./...",
                    ],
                }
            )

        if (
            "python application" in project_type
            or "python" in test_frameworks
        ):

            if "pytest" in test_frameworks:

                commands.append(
                    {
                        "type": "test",
                        "command": [
                            sys.executable,
                            "-m",
                            "pytest",
                        ],
                    }
                )

            elif analysis.get("test_files"):

                commands.append(
                    {
                        "type": "test",
                        "command": [
                            sys.executable,
                            "-m",
                            "unittest",
                            "discover",
                            "tests",
                        ],
                    }
                )

            else:

                commands.append(
                    {
                        "type": "syntax",
                        "command": [
                            sys.executable,
                            "-m",
                            "compileall",
                            "-q",
                            ".",
                        ],
                    }
                )

        if "flutter test" in test_frameworks:

            commands.append(
                {
                    "type": "test",
                    "command": [
                        "flutter",
                        "test",
                    ],
                }
            )

        if (
            "html/css web application"
            in project_type
            or "html web application"
            in project_type
        ):

            commands.append(
                {
                    "type": "static",
                    "command": None,
                }
            )

        if (
            "c++" in project_type.lower()
            and "cmake" in build_systems
        ):

            commands.append(
                {
                    "type": "build",
                    "command": [
                        "cmake",
                        "--build",
                        "build",
                    ],
                }
            )

        return commands

    @staticmethod
    def validate_static_project(
        repository_path: str,
        analysis: dict,
    ) -> dict:

        files = analysis.get(
            "files",
            [],
        )

        checked_files = []

        for file_info in files:

            path = file_info.get("path")

            if not path:
                continue

            file_path = os.path.join(
                repository_path,
                path.replace(
                    "/",
                    os.sep,
                ),
            )

            if not os.path.isfile(file_path):

                return {
                    "passed": False,
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": (
                        f"Missing file: {path}"
                    ),
                    "command": None,
                    "validation_type": "static",
                }

            try:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8",
                    errors="strict",
                ) as file:
                    file.read()

                checked_files.append(path)

            except (
                OSError,
                UnicodeError,
            ) as exc:

                return {
                    "passed": False,
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": (
                        f"Unable to read {path}: "
                        f"{exc}"
                    ),
                    "command": None,
                    "validation_type": "static",
                }

        return {
            "passed": True,
            "exit_code": 0,
            "stdout": (
                f"Validated {len(checked_files)} "
                "project files successfully."
            ),
            "stderr": "",
            "command": "static-project-validation",
            "validation_type": "static",
        }

    @staticmethod
    def run_command(
        repository_path: str,
        command: list,
        validation_type: str,
        timeout: int,
    ) -> dict:

        print(
            "[Validation] Running: "
            + " ".join(command)
        )

        environment = {
            **os.environ,
            "PYTHONUNBUFFERED": "1",
        }

        scripts_path = os.path.join(
            repository_path,
            "scripts",
        )

        existing_pythonpath = environment.get(
            "PYTHONPATH",
            "",
        )

        if os.path.isdir(scripts_path):

            environment["PYTHONPATH"] = (
                scripts_path
                + os.pathsep
                + existing_pythonpath
                if existing_pythonpath
                else scripts_path
            )

        try:

            result = subprocess.run(
                command,
                cwd=repository_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=environment,
            )

            print(
                "[Validation] Exit code: "
                f"{result.returncode}"
            )

            return {
                "passed": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(command),
                "validation_type": validation_type,
            }

        except subprocess.TimeoutExpired as exc:

            stdout = (
                exc.stdout.decode(errors="ignore")
                if isinstance(exc.stdout, bytes)
                else exc.stdout or ""
            )

            stderr = (
                exc.stderr.decode(errors="ignore")
                if isinstance(exc.stderr, bytes)
                else exc.stderr or ""
            )

            return {
                "passed": False,
                "exit_code": None,
                "stdout": stdout,
                "stderr": stderr,
                "command": " ".join(command),
                "timeout": True,
                "validation_type": validation_type,
            }

        except FileNotFoundError:

            return {
                "passed": False,
                "exit_code": None,
                "stdout": "",
                "stderr": (
                    "Required command was not found: "
                    + command[0]
                ),
                "command": " ".join(command),
                "validation_type": validation_type,
            }

    @staticmethod
    def run_tests(
        repository_path: str,
        analysis: dict,
        timeout: int = 120,
    ) -> dict:

        validation_commands = (
            TestRunnerService.detect_validation_commands(
                repository_path,
                analysis,
            )
        )

        if not validation_commands:

            return {
                "passed": True,
                "exit_code": 0,
                "stdout": "",
                "stderr": "",
                "command": None,
                "validation_type": "none",
                "skipped": True,
                "reason": (
                    "No supported validation system "
                    "was detected"
                ),
            }

        for validation in validation_commands:

            validation_type = validation["type"]
            command = validation["command"]

            if validation_type == "static":

                result = (
                    TestRunnerService.validate_static_project(
                        repository_path,
                        analysis,
                    )
                )

            else:

                result = (
                    TestRunnerService.run_command(
                        repository_path,
                        command,
                        validation_type,
                        timeout,
                    )
                )

            if not result["passed"]:

                return result

        return {
            "passed": True,
            "exit_code": 0,
            "stdout": (
                "All detected validation checks passed."
            ),
            "stderr": "",
            "command": "multiple",
            "validation_type": "multiple",
            "skipped": False,
        }