import os

from app.services.repository_service import RepositoryService
from app.services.git_service import GitService


REPOSITORY_URL = (
    "https://github.com/Yash045-ycs/portfolio"
)

BRANCH_NAME = "syntra/push-test"


repository_path = RepositoryService.clone_repository(
    REPOSITORY_URL
)

try:

    print()
    print("========== CREATE BRANCH ==========")

    branch = GitService.create_branch(
        repository_path,
        BRANCH_NAME,
    )

    print(branch)

    test_file = os.path.join(
        repository_path,
        "syntra_push_test.txt",
    )

    with open(
        test_file,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            "Syntra GitHub push integration test\n"
        )

    print()
    print("========== COMMIT ==========")

    commit = GitService.commit_changes(
        repository_path,
        "test: verify Syntra GitHub push",
    )

    print(commit)

    if not commit["success"]:
        raise RuntimeError(
            "Commit failed"
        )

    print()
    print("========== PUSH ==========")

    push = GitService.push_branch(
        repository_path,
        BRANCH_NAME,
    )

    print(push)

finally:

    RepositoryService.cleanup_repository(
        repository_path
    )