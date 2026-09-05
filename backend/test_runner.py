from app.services.repository_service import RepositoryService
from app.services.test_runner_service import TestRunnerService


REPOSITORY_URL = (
    "https://github.com/public-apis/public-apis"
)


repository_path = RepositoryService.clone_repository(
    REPOSITORY_URL
)

try:
    result = TestRunnerService.run_tests(
        repository_path
    )

    print()
    print("TEST RESULT")
    print("Passed:", result["passed"])
    print("Exit code:", result["exit_code"])

    print()
    print("STDOUT")
    print(result["stdout"])

    print()
    print("STDERR")
    print(result["stderr"])

finally:
    RepositoryService.cleanup_repository(
        repository_path
    )