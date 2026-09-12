from pathlib import Path

from app.services.code_change_applier_service import (
    CodeChangeApplierService,
)

repository = Path("rag_test_repo").resolve()
test_file = repository / "main.py"

original_content = test_file.read_text(
    encoding="utf-8"
)

print("TEST 1: Valid modification")

result = CodeChangeApplierService.apply_changes(
    repository_path=str(repository),
    changes=[
        {
            "file_path": "main.py",
            "action": "modify",
            "content": original_content
            + "\n\nprint('Syntra test')\n",
        }
    ],
)

print(result)
print("main.py modified:", test_file.read_text(
    encoding="utf-8"
).endswith("print('Syntra test')\n"))

backup_file = repository / "main.py.syntra_backup"

print("backup exists:", backup_file.exists())

test_file.write_text(
    original_content,
    encoding="utf-8",
)

if backup_file.exists():
    backup_file.unlink()

print()
print("TEST 2: Path traversal")

try:
    CodeChangeApplierService.apply_changes(
        repository_path=str(repository),
        changes=[
            {
                "file_path": "../outside.py",
                "action": "modify",
                "content": "malicious",
            }
        ],
    )
    print("FAILED: path traversal was allowed")
except ValueError as exc:
    print("PASSED:", exc)

print()
print("TEST 3: Protected .env")

try:
    CodeChangeApplierService.apply_changes(
        repository_path=str(repository),
        changes=[
            {
                "file_path": ".env",
                "action": "modify",
                "content": "SECRET=malicious",
            }
        ],
    )
    print("FAILED: .env modification was allowed")
except ValueError as exc:
    print("PASSED:", exc)

print()
print("All security tests completed")
