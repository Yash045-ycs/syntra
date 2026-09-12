from pathlib import Path

from app.services.diff_security_service import DiffSecurityService


repository = Path("rag_test_repo").resolve()
test_file = repository / "main.py"

original_content = test_file.read_text(
    encoding="utf-8"
)

print("TEST 1: Legitimate planned change")

test_file.write_text(
    original_content
    + "\n\nprint('Syntra change')\n",
    encoding="utf-8",
)

result = DiffSecurityService.validate(
    repository_path=str(repository),
    planned_files=["main.py"],
)

print("Safe:", result["safe"])
print("Changed files:", result["changed_files"])
print("Unexpected files:", result["unexpected_files"])
print("Protected files:", result["protected_files"])
print("Secrets:", result["secret_matches"])
print("Changed lines:", result["changed_lines"])

test_file.write_text(
    original_content,
    encoding="utf-8",
)

print()
print("TEST 2: Secret detection")

test_file.write_text(
    original_content
    + "\nAPI_KEY = 'AIza123456789012345678901'\n",
    encoding="utf-8",
)

result = DiffSecurityService.validate(
    repository_path=str(repository),
    planned_files=["main.py"],
)

print("Safe:", result["safe"])
print("Secret detected:", bool(result["secret_matches"]))

test_file.write_text(
    original_content,
    encoding="utf-8",
)

print()
print("TEST 3: Unexpected file")

unexpected_file = repository / "unexpected.py"

unexpected_file.write_text(
    "print('unexpected change')\n",
    encoding="utf-8",
)

result = DiffSecurityService.validate(
    repository_path=str(repository),
    planned_files=["main.py"],
)

print("Safe:", result["safe"])
print("Unexpected files:", result["unexpected_files"])

unexpected_file.unlink()

print()
print("All diff security tests completed")
