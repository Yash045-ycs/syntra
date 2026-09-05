from app.services.github_service import GitHubService


OWNER = "Yash045-ycs"
REPOSITORY = "portfolio"


result = GitHubService.get_repository(
    OWNER,
    REPOSITORY,
)

print()
print("========== GITHUB REPOSITORY ==========")
print("Repository:", result["full_name"])
print("Owner:", result["owner"])
print("Default branch:", result["default_branch"])
print("Private:", result["private"])
print("URL:", result["html_url"])