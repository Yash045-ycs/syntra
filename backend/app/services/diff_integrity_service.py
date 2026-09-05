import os
import subprocess


class DiffIntegrityService:

    @staticmethod
    def normalize_path(path: str) -> str:
        return os.path.normpath(
            path
        ).replace("\\", "/")

    @classmethod
    def get_changed_files(
        cls,
        repository_path: str,
    ) -> list[str]:

        result = subprocess.run(
            [
                "git",
                "status",
                "--short",
            ],
            cwd=repository_path,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Failed to inspect Git status: "
                + result.stderr.strip()
            )

        files = set()

        for line in result.stdout.splitlines():

            if not line.strip():
                continue

            status = line[:2]
            path = line[3:].strip()

            if " -> " in path:
                path = path.split(
                    " -> ",
                    1,
                )[1]

            if status[0] == "?" or status[1] == "?":
                files.add(
                    cls.normalize_path(path)
                )
                continue

            files.add(
                cls.normalize_path(path)
            )

        return sorted(files)

    @classmethod
    def validate(
        cls,
        repository_path: str,
        expected_files: list[str],
    ) -> dict:

        expected = {
            cls.normalize_path(path)
            for path in expected_files
        }

        actual = set(
            cls.get_changed_files(
                repository_path
            )
        )

        unexpected_files = sorted(
            actual - expected
        )

        missing_files = sorted(
            expected - actual
        )

        passed = not unexpected_files

        return {
            "passed": passed,
            "expected_files": sorted(expected),
            "changed_files": sorted(actual),
            "unexpected_files": unexpected_files,
            "missing_files": missing_files,
            "reason": (
                "Git changes match the allowed file set"
                if passed
                else "Git changes contain unexpected files"
            ),
        }