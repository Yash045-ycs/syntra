import {
  Bot,
  ChevronRight,
  CircleCheck,
  FolderGit2,
  GitPullRequest,
  Loader2,
  Plus,
  Sparkles,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getAgentRuns,
  getProjects,
  runAgent,
} from "../services/api";

type Project = {
  id: number;
  name: string;
  repository_url: string;
  owner_id: number;
};

type AgentRun = {
  id: number;
  project_id: number;
  status: string;
  user_request: string;
  goal: string | null;
  validation_status: string | null;
  test_status: string | null;
  pr_number: number | null;
  pr_url: string | null;
  created_at: string;
  completed_at: string | null;
};

type Activity = {
  id: string;
  icon: React.ElementType;
  title: string;
  description: string;
  time: string;
};

function formatRelativeTime(value: string) {
  const date = new Date(
    value.endsWith("Z") ? value : `${value}Z`,
  );

  const now = new Date();

  const seconds = Math.floor(
    (now.getTime() - date.getTime()) / 1000,
  );

  if (seconds < 60) {
    return "Just now";
  }

  const minutes = Math.floor(seconds / 60);

  if (minutes < 60) {
    return `${minutes} min ago`;
  }

  const hours = Math.floor(minutes / 60);

  if (hours < 24) {
    return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  }

  const days = Math.floor(hours / 24);

  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function getLanguage(repositoryUrl: string) {
  const repositoryName = repositoryUrl
    .split("/")
    .filter(Boolean)
    .pop()
    ?.toLowerCase();

  if (!repositoryName) {
    return "Repository";
  }

  return "Repository";
}

function getProjectStatus(projectRuns: AgentRun[]) {
  const latestRun = projectRuns[0];

  if (!latestRun) {
    return "No runs yet";
  }

  if (
    latestRun.status === "completed" ||
    latestRun.status === "approved"
  ) {
    return "Completed";
  }

  if (latestRun.status === "failed") {
    return "Failed";
  }

  return "Running";
}

function Dashboard() {
  const navigate = useNavigate();

  const [projects, setProjects] = useState<Project[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);

  const [loading, setLoading] = useState(true);
  const [showAgent, setShowAgent] = useState(false);
  const [startingAgent, setStartingAgent] = useState(false);

  const [selectedProjectId, setSelectedProjectId] =
    useState<number | null>(null);

  const [userRequest, setUserRequest] = useState("");
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const projectData = (await getProjects()) as Project[];

      setProjects(projectData);

      const allRuns: AgentRun[] = [];

      for (const project of projectData) {
        try {
          const projectRuns = (await getAgentRuns(
            project.id,
          )) as AgentRun[];

          allRuns.push(...projectRuns);
        } catch {
          continue;
        }
      }

      allRuns.sort(
        (a, b) =>
          new Date(
            b.created_at.endsWith("Z")
              ? b.created_at
              : `${b.created_at}Z`,
          ).getTime() -
          new Date(
            a.created_at.endsWith("Z")
              ? a.created_at
              : `${a.created_at}Z`,
          ).getTime(),
      );

      setRuns(allRuns);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load dashboard",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  function openAgent() {
    setError("");
    setUserRequest("");

    if (projects.length > 0) {
      setSelectedProjectId(projects[0].id);
    } else {
      setSelectedProjectId(null);
    }

    setShowAgent(true);
  }

  async function handleRunAgent(event: React.FormEvent) {
    event.preventDefault();

    if (!selectedProjectId || !userRequest.trim()) {
      return;
    }

    try {
      setStartingAgent(true);
      setError("");

      await runAgent(
        selectedProjectId,
        userRequest.trim(),
      );

      setShowAgent(false);
      setUserRequest("");

      navigate("/runs");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to start agent run",
      );
    } finally {
      setStartingAgent(false);
    }
  }

  const successfulRuns = runs.filter(
    (run) =>
      run.status === "completed" ||
      run.status === "approved",
  ).length;

  const completedRuns = runs.filter(
    (run) =>
      run.status === "completed" ||
      run.status === "approved",
  ).length;

  const successRate =
    runs.length > 0
      ? Math.round((successfulRuns / runs.length) * 100)
      : 0;

  const pullRequests = runs.filter(
    (run) => run.pr_url,
  ).length;

  const awaitingReview = runs.filter(
    (run) =>
      run.status === "completed" &&
      run.pr_url,
  ).length;

  const projectRuns = useMemo(() => {
    const map = new Map<number, AgentRun[]>();

    for (const run of runs) {
      const current = map.get(run.project_id) ?? [];

      current.push(run);

      map.set(run.project_id, current);
    }

    return map;
  }, [runs]);

  const activities: Activity[] = runs
    .slice(0, 5)
    .map((run) => {
      const project = projects.find(
        (item) => item.id === run.project_id,
      );

      if (run.pr_url) {
        return {
          id: `pr-${run.id}`,
          icon: GitPullRequest,
          title: "Pull request created",
          description: `${
            project?.name ?? "Project"
          } · PR #${run.pr_number}`,
          time: formatRelativeTime(run.created_at),
        };
      }

      if (
        run.status === "completed" ||
        run.status === "approved"
      ) {
        return {
          id: `completed-${run.id}`,
          icon: CircleCheck,
          title: "Agent run completed",
          description:
            run.goal ||
            run.user_request ||
            `${
              project?.name ?? "Project"
            } completed successfully`,
          time: formatRelativeTime(run.created_at),
        };
      }

      if (run.status === "failed") {
        return {
          id: `failed-${run.id}`,
          icon: Bot,
          title: "Agent run failed",
          description: `${
            project?.name ?? "Project"
          } · ${run.user_request}`,
          time: formatRelativeTime(run.created_at),
        };
      }

      return {
        id: `running-${run.id}`,
        icon: Bot,
        title: "Agent run started",
        description: `${
          project?.name ?? "Project"
        } · ${run.user_request}`,
        time: formatRelativeTime(run.created_at),
      };
    });

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      <section className="mb-8">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div>
            <div className="mb-2 flex items-center gap-2 text-xs font-medium syntra-text-muted">
              <Sparkles size={13} />
              AUTONOMOUS ENGINEERING
            </div>

            <h1 className="text-3xl font-semibold tracking-tight syntra-text">
              Good evening, Yash.
            </h1>

            <p className="mt-2 max-w-xl text-sm leading-6 syntra-text-muted">
              Build, modify and validate software with an AI
              agent that understands your codebase.
            </p>
          </div>

          <button
            onClick={() => navigate("/projects")}
            className="flex items-center justify-center gap-2 rounded-lg bg-black px-4 py-2.5 text-sm font-medium text-white transition hover:opacity-80 dark:bg-white dark:text-black"
          >
            <Plus size={16} />
            New Project
          </button>
        </div>
      </section>

      {error && !showAgent && (
        <div className="mb-6 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          {error}
        </div>
      )}

      <section className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Projects"
          value={loading ? "—" : String(projects.length)}
          detail="Connected repositories"
          icon={FolderGit2}
        />

        <StatCard
          label="Agent Runs"
          value={loading ? "—" : String(runs.length)}
          detail={`${completedRuns} completed successfully`}
          icon={Bot}
        />

        <StatCard
          label="Pull Requests"
          value={loading ? "—" : String(pullRequests)}
          detail={`${awaitingReview} awaiting review`}
          icon={GitPullRequest}
        />

        <StatCard
          label="Success Rate"
          value={loading ? "—" : `${successRate}%`}
          detail="Across recorded agent runs"
          icon={CircleCheck}
        />
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <section className="rounded-2xl border syntra-card">
          <div className="flex items-center justify-between border-b syntra-border px-5 py-4">
            <div>
              <h2 className="text-sm font-semibold syntra-text">
                Projects
              </h2>

              <p className="mt-1 text-xs syntra-text-faint">
                Repositories connected to Syntra
              </p>
            </div>

            <button
              onClick={() => navigate("/projects")}
              className="text-xs syntra-text-muted transition hover:opacity-70"
            >
              View all
            </button>
          </div>

          {loading ? (
            <div className="px-5 py-10 text-center text-xs syntra-text-faint">
              Loading projects...
            </div>
          ) : projects.length === 0 ? (
            <div className="px-5 py-10 text-center">
              <FolderGit2
                size={24}
                className="mx-auto syntra-text-faint"
              />

              <p className="mt-3 text-sm syntra-text-muted">
                No projects connected yet.
              </p>

              <button
                onClick={() => navigate("/projects")}
                className="mt-4 text-xs syntra-text-secondary transition hover:opacity-70"
              >
                Add your first project
              </button>
            </div>
          ) : (
            <div className="divide-y syntra-border">
              {projects.slice(0, 5).map((project) => {
                const projectRunList =
                  projectRuns.get(project.id) ?? [];

                return (
                  <ProjectRow
                    key={project.id}
                    project={project}
                    status={getProjectStatus(
                      projectRunList,
                    )}
                    language={getLanguage(
                      project.repository_url,
                    )}
                    onClick={() =>
                      navigate(
                        `/runs?project=${project.id}`,
                      )
                    }
                  />
                );
              })}
            </div>
          )}
        </section>

        <section className="rounded-2xl border syntra-card">
          <div className="border-b syntra-border px-5 py-4">
            <h2 className="text-sm font-semibold syntra-text">
              Recent activity
            </h2>

            <p className="mt-1 text-xs syntra-text-faint">
              Latest agent events
            </p>
          </div>

          {loading ? (
            <div className="px-5 py-10 text-center text-xs syntra-text-faint">
              Loading activity...
            </div>
          ) : activities.length === 0 ? (
            <div className="px-5 py-10 text-center text-xs syntra-text-faint">
              No agent activity yet.
            </div>
          ) : (
            <div className="divide-y syntra-border">
              {activities.map((activity) => {
                const Icon = activity.icon;

                return (
                  <div
                    key={activity.id}
                    className="flex gap-3 px-5 py-4"
                  >
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border syntra-border-secondary bg-black/[0.025]">
                      <Icon
                        size={14}
                        className="syntra-text-secondary"
                      />
                    </div>

                    <div className="min-w-0">
                      <div className="text-xs font-medium syntra-text-secondary">
                        {activity.title}
                      </div>

                      <div className="mt-1 line-clamp-2 text-xs leading-5 syntra-text-faint">
                        {activity.description}
                      </div>

                      <div className="mt-1.5 text-[10px] syntra-text-faint">
                        {activity.time}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>

      <section className="mt-6 overflow-hidden rounded-2xl border syntra-card">
        <div className="flex flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border syntra-border-secondary bg-black/[0.025]">
              <Bot
                size={18}
                className="syntra-text-secondary"
              />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold syntra-text">
                  Start an agent run
                </h2>

                <span className="rounded-full border border-emerald-500/20 bg-emerald-500/5 px-2 py-0.5 text-[10px] text-emerald-500">
                  Ready
                </span>
              </div>

              <p className="mt-1 text-xs leading-5 syntra-text-faint">
                Describe a change in natural language and let
                Syntra analyze, modify and validate your
                repository.
              </p>
            </div>
          </div>

          <button
            onClick={openAgent}
            disabled={
              loading || projects.length === 0
            }
            className="flex items-center justify-center gap-2 whitespace-nowrap rounded-lg border syntra-border-secondary bg-black/[0.025] px-4 py-2.5 text-xs font-medium syntra-text-secondary transition hover:bg-black/[0.05] disabled:cursor-not-allowed disabled:opacity-40"
          >
            Open Agent
            <ChevronRight size={14} />
          </button>
        </div>
      </section>

      {showAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-2xl border syntra-border bg-[var(--bg-primary)] p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl border syntra-border-secondary bg-black/[0.025]">
                    <Bot
                      size={17}
                      className="syntra-text-secondary"
                    />
                  </div>

                  <h2 className="text-xl font-semibold syntra-text">
                    Start Agent Run
                  </h2>
                </div>

                <p className="mt-3 text-sm leading-6 syntra-text-muted">
                  Tell Syntra what you want changed in your
                  codebase.
                </p>
              </div>

              <button
                onClick={() => setShowAgent(false)}
                disabled={startingAgent}
                className="rounded-lg p-2 syntra-text-muted transition syntra-hover disabled:opacity-50"
              >
                <X size={18} />
              </button>
            </div>

            {error && (
              <div className="mt-5 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-500">
                {error}
              </div>
            )}

            {projects.length === 0 ? (
              <div className="mt-6 rounded-xl border border-dashed syntra-border-secondary bg-black/[0.025] px-5 py-8 text-center">
                <p className="text-sm syntra-text-muted">
                  Add a project before starting an agent run.
                </p>

                <button
                  onClick={() => navigate("/projects")}
                  className="mt-4 rounded-lg bg-black px-4 py-2.5 text-sm font-medium text-white transition hover:opacity-80 dark:bg-white dark:text-black"
                >
                  Add Project
                </button>
              </div>
            ) : (
              <form
                onSubmit={handleRunAgent}
                className="mt-6 space-y-5"
              >
                <div>
                  <label className="mb-2 block text-sm font-medium syntra-text-secondary">
                    Project
                  </label>

                  <select
                    value={selectedProjectId ?? ""}
                    onChange={(event) =>
                      setSelectedProjectId(
                        event.target.value
                          ? Number(event.target.value)
                          : null,
                      )
                    }
                    disabled={startingAgent}
                    className="syntra-input w-full rounded-xl border px-4 py-3 text-sm outline-none transition focus:border-zinc-500 disabled:opacity-50"
                  >
                    {projects.map((project) => (
                      <option
                        key={project.id}
                        value={project.id}
                      >
                        {project.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium syntra-text-secondary">
                    What should Syntra change?
                  </label>

                  <textarea
                    value={userRequest}
                    onChange={(event) =>
                      setUserRequest(event.target.value)
                    }
                    disabled={startingAgent}
                    rows={6}
                    placeholder="Example: Add input validation to the user registration endpoint and update the existing tests."
                    className="syntra-input w-full resize-none rounded-xl border px-4 py-3 text-sm leading-6 outline-none transition placeholder:text-zinc-500 focus:border-zinc-500 disabled:opacity-50"
                    required
                  />

                  <p className="mt-2 text-xs syntra-text-faint">
                    Be specific about the behavior you want.
                    Syntra will inspect the relevant code before
                    making changes.
                  </p>
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAgent(false)}
                    disabled={startingAgent}
                    className="rounded-xl border syntra-border-secondary px-4 py-2.5 text-sm font-medium syntra-text-secondary transition hover:bg-black/[0.05] disabled:opacity-50"
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    disabled={
                      startingAgent ||
                      !selectedProjectId ||
                      !userRequest.trim()
                    }
                    className="flex items-center gap-2 rounded-xl bg-black px-4 py-2.5 text-sm font-medium text-white transition hover:opacity-80 dark:bg-white dark:text-black disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {startingAgent && (
                      <Loader2
                        size={15}
                        className="animate-spin"
                      />
                    )}

                    {startingAgent
                      ? "Starting..."
                      : "Run Syntra"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  detail,
  icon: Icon,
}: {
  label: string;
  value: string;
  detail: string;
  icon: React.ElementType;
}) {
  return (
    <div className="rounded-2xl border syntra-card p-5">
      <div className="mb-5 flex items-center justify-between">
        <span className="text-xs syntra-text-muted">
          {label}
        </span>

        <Icon
          size={16}
          className="syntra-text-faint"
        />
      </div>

      <div className="text-2xl font-semibold tracking-tight syntra-text">
        {value}
      </div>

      <div className="mt-1 text-[11px] syntra-text-faint">
        {detail}
      </div>
    </div>
  );
}

function ProjectRow({
  project,
  status,
  language,
  onClick,
}: {
  project: Project;
  status: string;
  language: string;
  onClick: () => void;
}) {
  const repo = project.repository_url
    .replace("https://github.com/", "")
    .replace(".git", "");

  return (
    <button
      onClick={onClick}
      className="flex w-full items-center gap-4 px-5 py-4 text-left transition hover:bg-black/[0.025]"
    >
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border syntra-border-secondary bg-black/[0.025]">
        <FolderGit2
          size={16}
          className="syntra-text-secondary"
        />
      </div>

      <div className="min-w-0 flex-1">
        <div className="text-xs font-medium syntra-text-secondary">
          {project.name}
        </div>

        <div className="mt-1 truncate text-[11px] syntra-text-faint">
          {repo}
        </div>
      </div>

      <div className="hidden text-right sm:block">
        <div className="text-[11px] syntra-text-muted">
          {language}
        </div>
      </div>

      <span className="hidden rounded-full border syntra-border-secondary px-2 py-1 text-[10px] syntra-text-muted sm:block">
        {status}
      </span>

      <ChevronRight
        size={14}
        className="syntra-text-faint"
      />
    </button>
  );
}

export default Dashboard;