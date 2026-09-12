from app.services.code_repair_service import CodeRepairService


source_files = {
    "main.py": """def calculate_total(price, tax):
    return price + (price * tax)
""",
    "test_main.py": """from main import calculate_total


def test_calculate_total():
    assert calculate_total(100, 0.10) == 111
""",
}

plan = {
    "goal": "Update calculate_total so the requested total calculation is correct.",
    "files_to_modify": [
        {
            "file_path": "other.py",
            "reason": "The calculation needs correction.",
            "changes": [
                "Fix calculate_total to satisfy the requested behavior."
            ],
        }
    ],
    "files_to_create": [],
    "risks": [],
    "validation": [
        "Run pytest."
    ],
    "assumptions": [],
}

failure_output = """
FAILED test_main.py::test_calculate_total

E       assert 110.0 == 111
E        +  where 110.0 = calculate_total(100, 0.1)

test_main.py:5: AssertionError
"""

result = CodeRepairService.generate_repair(
    user_request="Fix the total calculation so the test passes.",
    plan=plan,
    failure_output=failure_output,
    source_files=source_files,
)

print(result)