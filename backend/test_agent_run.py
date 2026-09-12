from app.services.agent_run_service import AgentRunService

REPOSITORY_URL = "https://github.com/Yash045-ycs/rag_test_repo"
PROJECT_ID = 4
USER_ID = 3
INSTALLATION_ID = 159244944

USER_REQUEST = (
    "Add a shipping cost parameter to calculate_total "
    "and include it in the returned total"
)

result = AgentRunService.run(
    repository_url=REPOSITORY_URL,
    installation_id=INSTALLATION_ID,
    project_id=PROJECT_ID,
    user_id=USER_ID,
    user_request=USER_REQUEST,
)

print("\n========== AGENT RUN RESULT ==========\n")
print(result)
print("\n========== END ==========\n")