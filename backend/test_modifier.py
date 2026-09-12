from app.services.code_modifier_service import CodeModifierService

source_files = {
    "main.py": """
def calculate_total(price, tax):
    return price + (price * tax)


def calculate_discount(price, discount):
    return price - (price * discount)
"""
}

plan = {
    "goal": "Add a shipping cost to the total price calculation.",
    "files_to_modify": [
        {
            "file_path": "main.py",
            "reason": "The total calculation is implemented here.",
            "changes": [
                "Update calculate_total to accept shipping.",
                "Add shipping to the final total."
            ]
        }
    ],
    "files_to_create": [],
    "risks": [],
    "validation": [
        "Verify calculate_total includes shipping."
    ],
    "assumptions": [
        "shipping is a numeric value."
    ]
}

result = CodeModifierService.generate_changes(
    user_request="Add shipping cost to the total price calculation.",
    plan=plan,
    source_files=source_files,
)

print(result)
