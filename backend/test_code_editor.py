import json

from app.services.repository_service import RepositoryService
from app.services.scanner_service import ScannerService
from app.services.context_service import CodebaseContextService
from app.services.planner_service import PlannerService
from app.services.code_editor_service import CodeEditorService


REPOSITORY_URL = "https://github.com/public-apis/public-apis"

CHANGE_REQUEST = (
    "Make the link checker run concurrently to improve performance."
)


print("[Test] Cloning repository")

repository_path = RepositoryService.clone_repository(
    REPOSITORY_URL
)

try:
    print("[Test] Scanning repository")

    analysis = ScannerService.scan_repository(
        repository_path
    )

    print(
        f"[Test] Files: {analysis['total_files']}"
    )

    print(
        f"[Test] Lines: {analysis['total_lines']}"
    )

    print("[Test] Building context")

    context = CodebaseContextService.build_context(
        repository_path,
        analysis,
    )

    print(
        f"[Test] Context files: "
        f"{context['files_in_context']}"
    )

    print("[Test] Creating plan")

    plan = PlannerService.create_plan(
        CHANGE_REQUEST,
        context,
    )

    print("[Test] Plan generated")

    print(
        json.dumps(
            plan,
            indent=2,
        )
    )

    print("[Test] Generating code changes")

    changes = CodeEditorService.generate_changes(
        CHANGE_REQUEST,
        plan,
        context,
    )

    print("[Test] Code changes generated")

    print(
        json.dumps(
            {
                "files": [
                    {
                        "path": change["path"],
                        "action": change["action"],
                        "content_length": len(
                            change["content"]
                        ),
                    }
                    for change in changes.get(
                        "changes",
                        [],
                    )
                ]
            },
            indent=2,
        )
    )

    print("[Test] Applying changes")

    applied_files = CodeEditorService.apply_changes(
        repository_path,
        changes,
    )

    print("[Test] Changes applied")

    print(
        json.dumps(
            {
                "applied_files": applied_files
            },
            indent=2,
        )
    )

finally:
    RepositoryService.cleanup_repository(
        repository_path
    )