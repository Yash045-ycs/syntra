import os
import re


class CodeChunkerService:

    MAX_CHUNK_LINES = 80
    OVERLAP_LINES = 10
    MIN_CHUNK_LINES = 5

    SUPPORTED_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".cpp",
        ".cc",
        ".cxx",
        ".c",
        ".h",
        ".hpp",
        ".dart",
        ".go",
        ".rs",
        ".kt",
        ".kts",
        ".swift",
        ".php",
        ".rb",
        ".cs",
        ".html",
        ".css",
        ".scss",
        ".sql",
        ".sh",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".xml",
    }

    @classmethod
    def chunk_file(
        cls,
        file_path: str,
        content: str,
    ) -> list[dict]:

        if not content.strip():
            return []

        extension = os.path.splitext(file_path)[1].lower()

        if extension not in cls.SUPPORTED_EXTENSIONS:
            return []

        lines = content.splitlines()

        if len(lines) <= cls.MAX_CHUNK_LINES:
            return [
                {
                    "file_path": file_path,
                    "chunk_index": 0,
                    "content": content,
                    "start_line": 1,
                    "end_line": len(lines),
                }
            ]

        boundaries = cls._find_boundaries(
            lines,
            extension,
        )

        chunks = []

        start = 0

        while start < len(lines):

            target_end = min(
                start + cls.MAX_CHUNK_LINES,
                len(lines),
            )

            boundary = cls._best_boundary(
                boundaries,
                start,
                target_end,
            )

            end = boundary if boundary is not None else target_end

            if end <= start:
                end = target_end

            chunk_lines = lines[start:end]

            if len(chunk_lines) >= cls.MIN_CHUNK_LINES:
                chunks.append(
                    {
                        "file_path": file_path,
                        "chunk_index": len(chunks),
                        "content": "\n".join(chunk_lines),
                        "start_line": start + 1,
                        "end_line": end,
                    }
                )

            if end >= len(lines):
                break

            next_start = max(
                end - cls.OVERLAP_LINES,
                start + 1,
            )

            start = next_start

        return chunks

    @classmethod
    def chunk_files(
        cls,
        files: dict[str, str],
    ) -> list[dict]:

        chunks = []

        for file_path, content in files.items():
            chunks.extend(
                cls.chunk_file(
                    file_path,
                    content,
                )
            )

        return chunks

    @classmethod
    def _find_boundaries(
        cls,
        lines: list[str],
        extension: str,
    ) -> list[int]:

        boundaries = []

        patterns = cls._get_boundary_patterns(
            extension
        )

        for index, line in enumerate(lines):

            stripped = line.strip()

            if not stripped:
                continue

            for pattern in patterns:
                if re.search(
                    pattern,
                    stripped,
                ):
                    boundaries.append(index + 1)
                    break

        return boundaries

    @classmethod
    def _best_boundary(
        cls,
        boundaries: list[int],
        start: int,
        target_end: int,
    ) -> int | None:

        candidates = [
            boundary
            for boundary in boundaries
            if start < boundary <= target_end
        ]

        if not candidates:
            return None

        return max(candidates)

    @staticmethod
    def _get_boundary_patterns(
        extension: str,
    ) -> list[str]:

        if extension == ".py":
            return [
                r"^(async\s+)?def\s+",
                r"^class\s+",
            ]

        if extension in {
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
        }:
            return [
                r"^(export\s+)?(async\s+)?function\s+",
                r"^(export\s+)?class\s+",
                r"^(export\s+)?const\s+\w+\s*=",
                r"^(export\s+)?default\s+",
            ]

        if extension in {
            ".java",
            ".kt",
            ".kts",
            ".cs",
        }:
            return [
                r"^(public|private|protected|static|\s)+class\s+",
                r"^(public|private|protected|static|\s)+interface\s+",
                r"^(public|private|protected|static|\s)+.*\(",
            ]

        if extension in {
            ".cpp",
            ".cc",
            ".cxx",
            ".c",
            ".h",
            ".hpp",
        }:
            return [
                r"^(class|struct)\s+",
                r"^(template\s*<.*>)?\s*\w[\w:*&<>\s]*\s+\w+\s*\(",
                r"^namespace\s+",
            ]

        if extension == ".dart":
            return [
                r"^(abstract\s+)?class\s+",
                r"^(Future|Stream|void|String|int|double|bool|dynamic)\s+",
                r"^Widget\s+",
            ]

        if extension in {
            ".go",
        }:
            return [
                r"^func\s+",
                r"^type\s+",
            ]

        if extension == ".rs":
            return [
                r"^(pub\s+)?fn\s+",
                r"^(pub\s+)?struct\s+",
                r"^(pub\s+)?enum\s+",
                r"^(pub\s+)?trait\s+",
                r"^impl\s+",
            ]

        if extension in {
            ".swift",
        }:
            return [
                r"^(public\s+|private\s+|internal\s+)?(class|struct|enum|protocol)\s+",
                r"^(public\s+|private\s+|internal\s+)?func\s+",
            ]

        if extension in {
            ".php",
            ".rb",
        }:
            return [
                r"^(public\s+|private\s+|protected\s+)?function\s+",
                r"^class\s+",
                r"^module\s+",
                r"^def\s+",
            ]

        if extension in {
            ".html",
            ".xml",
        }:
            return [
                r"^<(!DOCTYPE|html|head|body|main|section|article|script|style|div)",
            ]

        if extension in {
            ".css",
            ".scss",
        }:
            return [
                r"^[^{]+\{",
            ]

        if extension == ".sql":
            return [
                r"^(CREATE|ALTER|DROP|SELECT|INSERT|UPDATE|DELETE|WITH)\s+",
            ]

        if extension in {
            ".md",
        }:
            return [
                r"^#{1,6}\s+",
            ]

        return []