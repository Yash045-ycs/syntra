from app.services.code_repair_service import CodeRepairService


source_files = {
    "main.py": "def calculate_total(price, tax):\n    return price + (price * tax)\n"
}

plan = {
    "files_to_modify": [
        {
            "file_path": "main.py",
            "reason": "Test",
            "changes": ["Test"]
        }
    ],
    "files_to_create": [],
}

malicious_repair = {
    "diagnosis": "Test",
    "changes": [
        {
            "file_path": "other.py",
            "action": "modify",
            "reason": "Unauthorized modification",
            "content": "print('bad')"
        }
    ],
    "files_not_modified": [],
    "warnings": [],
}

try:
    CodeRepairService._validate_repair(
        malicious_repair,
        source_files,
        plan,
    )
    print("SECURITY TEST FAILED")
except RuntimeError as exc:
    print("SECURITY TEST PASSED")
    print(exc)