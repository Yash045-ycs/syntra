import os

from app.services.scanner_service import ScannerService


class CodebaseContextService:

    MAX_FILE_LINES = 800
    MAX_TOTAL_LINES = 6000

    IMPORTANT_FILES = {
        "readme.md",
        "requirements.txt",
        "pyproject.toml",
        "package.json",
        "go.mod",
        "cargo.toml",
        "pubspec.yaml",
        "pom.xml",
    }

    @classmethod
    def build_context(
        cls,
        repository_path: str,
        analysis: dict,
    ) -> dict:

        selected_files = []
        total_lines = 0

        files = analysis.get("files", [])

        priority_files = []
        normal_files = []

        for file_info in files:
            filename = os.path.basename(file_info["path"]).lower()

            if (
                filename in cls.IMPORTANT_FILES
                or file_info["path"] in analysis.get("entry_points", [])
                or file_info["path"] in analysis.get("test_files", [])
            ):
                priority_files.append(file_info)
            else:
                normal_files.append(file_info)

        ordered_files = priority_files + normal_files

        for file_info in ordered_files:

            if total_lines >= cls.MAX_TOTAL_LINES:
                break

            relative_path = file_info["path"]
            file_path = os.path.join(
                repository_path,
                relative_path.replace("/", os.sep),
            )

            try:
                with open(
                    file_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore",
                ) as file:
                    lines = file.readlines()

                if not lines:
                    continue

                remaining_lines = cls.MAX_TOTAL_LINES - total_lines
                max_lines = min(
                    cls.MAX_FILE_LINES,
                    remaining_lines,
                )

                content = "".join(lines[:max_lines])

                selected_files.append(
                    {
                        "path": relative_path,
                        "language": file_info["language"],
                        "lines": len(lines),
                        "content": content,
                        "truncated": len(lines) > max_lines,
                    }
                )

                total_lines += min(len(lines), max_lines)

            except (OSError, UnicodeError):
                continue

        return {
            "project_type": analysis.get("project_type"),
            "total_files": analysis.get("total_files", 0),
            "total_lines": analysis.get("total_lines", 0),
            "languages": analysis.get("languages", {}),
            "entry_points": analysis.get("entry_points", []),
            "test_files": analysis.get("test_files", []),
            "dependency_files": analysis.get("dependency_files", []),
            "files_in_context": len(selected_files),
            "lines_in_context": total_lines,
            "files": selected_files,
        }