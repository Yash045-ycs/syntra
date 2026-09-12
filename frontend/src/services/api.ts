const API_URL = "http://127.0.0.1:8000";

function getToken() {
return localStorage.getItem("syntra_token");
}

async function request<T>(
endpoint: string,
options: RequestInit = {},
): Promise<T> {
const token = getToken();

const headers = new Headers(options.headers);

headers.set("Content-Type", "application/json");

if (token) {
headers.set("Authorization", `Bearer ${token}`);
}

const response = await fetch(`${API_URL}${endpoint}`, {
...options,
headers,
});

if (!response.ok) {
let message = "Request failed";

try {
  const data = await response.json();
  message = data.detail || message;
} catch {
  message = response.statusText || message;
}

throw new Error(message);
}

return response.json();
}

export async function checkBackendHealth() {
return request<{ status: string }>("/api/health");
}

export async function login(email: string, password: string) {
const body = new URLSearchParams();

body.append("username", email);
body.append("password", password);

const response = await fetch(`${API_URL}/api/auth/login`, {
method: "POST",
headers: {
"Content-Type": "application/x-www-form-urlencoded",
},
body,
});

if (!response.ok) {
let message = "Login failed";

try {
  const data = await response.json();
  message = data.detail || message;
} catch {
  message = response.statusText || message;
}

throw new Error(message);

}

const data = await response.json();

localStorage.setItem("syntra_token", data.access_token);

return data;
}

export async function register(email: string, password: string) {
return request("/api/auth/register", {
method: "POST",
body: JSON.stringify({
email,
password,
}),
});
}

export async function getCurrentUser() {
return request("/api/auth/me");
}

export async function getGitHubAuthorizationUrl() {
  return request<{ authorization_url: string }>("/api/github/login");
}

export async function getProjects() {
return request("/api/projects");
}

export async function getProject(projectId: number) {
return request(`/api/projects/${projectId}`);
}

export async function createProject(
name: string,
repositoryUrl: string,
) {
return request("/api/projects", {
method: "POST",
body: JSON.stringify({
name,
repository_url: repositoryUrl,
}),
});
}

export async function deleteProject(projectId: number) {
return request(`/api/projects/${projectId}`, {
method: "DELETE",
});
}

export async function runAgent(
projectId: number,
userRequest: string,
) {
return request(`/api/projects/${projectId}/agent/run`, {
method: "POST",
body: JSON.stringify({
user_request: userRequest,
}),
});
}

export async function getAgentRuns(projectId: number) {
return request(`/api/projects/${projectId}/runs`);
}

export async function getAgentRun(
projectId: number,
runId: number,
) {
return request(`/api/projects/${projectId}/runs/${runId}`);
}

export async function getRunDiff(
projectId: number,
runId: number,
) {
return request(`/api/projects/${projectId}/runs/${runId}/diff`);
}

export async function approveAgentRun(
projectId: number,
runId: number,
) {
return request(`/api/projects/${projectId}/runs/${runId}/approve`, {
method: "POST",
});
}

export async function getRunPullRequest(
projectId: number,
runId: number,
) {
return request(`/api/projects/${projectId}/runs/${runId}/pr`);
}

export function logout() {
localStorage.removeItem("syntra_token");
}
