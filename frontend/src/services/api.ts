const API_URL = "http://127.0.0.1:8000";

export async function checkBackendHealth() {
  const response = await fetch(`${API_URL}/api/health`);

  if (!response.ok) {
    throw new Error("Backend request failed");
  }

  return response.json();
}