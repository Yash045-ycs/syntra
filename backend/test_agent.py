from app.services.agent_service import AgentService


REPOSITORY_URL = (
    "https://github.com/Yash045-ycs/portfolio"
)

CHANGE_REQUEST = (
    "Add a simple README section describing this project."
)


result = AgentService.execute(
    repository_url=REPOSITORY_URL,
    change_request=CHANGE_REQUEST,
)

print()
print("========== AGENT RESULT ==========")

print("Success:", result["success"])

print("Branch:", result["branch_name"])

print("Fix attempts:", result["fix_attempts"])

print()
print("Applied files:")

for file in result["applied_files"]:
    print("-", file)

print()
print("Test passed:")
print(result["test_result"]["passed"])

print()
print("Test exit code:")
print(result["test_result"]["exit_code"])

if result["git"]:

    print()
    print("========== GIT COMMIT ==========")

    print(
        result["git"]["commit"]["stdout"]
    )

    print()
    print("========== GIT DIFF ==========")

    print(
        result["git"]["diff"]["stdout"]
    )

    print()
    print("========== GIT PUSH ==========")

    print(
        result["git"]["push"]["stdout"]
    )

if result.get("github"):

    print()
    print("========== GITHUB PULL REQUEST ==========")

    print(
        "Repository:",
        result["github"]["repository"]["full_name"]
    )

    print(
        "PR:",
        result["github"]["pull_request"]["url"]
    )

    print(
        "Branch:",
        result["github"]["pull_request"]["head"]
    )

    print(
        "Base:",
        result["github"]["pull_request"]["base"]
    )

else:

    print()
    print("No GitHub pull request was created.")