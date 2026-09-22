import {
  Activity,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  ExternalLink,
  GitBranch,
  Loader2,
  Play,
  RefreshCw,
  Trash2,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  deleteProject,
  getAgentRuns,
  getProject,
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
  pr_number: number | null;
  pr_url: string | null;
  validation_status: string | null;
  test_status: string | null;
  created_at: string;
  completed_at: string | null;
};

function formatDate(value: string) {
  const date = new Date(
    value.endsWith("Z") ? value : `${value}Z`,
  );

  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function getStatusStyle(status: string) {
  switch (status.toLowerCase()) {
    case "completed":
    case "approved":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-400";

    case "failed":
      return "border-red-500/20 bg-red-500/10 text-red-400";

    case "running":
      return "border-yellow-500/20 bg-yellow-500/10 text-yellow-400";

    default:
      return "border-zinc-700 bg-zinc-800/60 text-zinc-400";
  }
}

export default function ProjectDetails() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [running, setRunning] = useState(false);

  const [request, setRequest] = useState("");
  const [error, setError] = useState("");

  async function loadProject() {
    if (!projectId) {
      setError("Invalid project.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");

      const [projectData, runsData] = await Promise.all([
        getProject(Number(projectId)),
        getAgentRuns(Number(projectId)),
      ]);

      setProject(projectData as Project);
      setRuns(runsData as AgentRun[]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load project",
      );
    } finally {
      setLoading(false);
    }
  }

  async function refreshProject() {
    if (!projectId) {
      return;
    }

    try {
      setRefreshing(true);
      setError("");

      const [projectData, runsData] = await Promise.all([
        getProject(Number(projectId)),
        getAgentRuns(Number(projectId)),
      ]);

      setProject(projectData as Project);
      setRuns(runsData as AgentRun[]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to refresh project",
      );
    } finally {
      setRefreshing(false);
    }
  }

  async function handleRunAgent() {
    if (!projectId || !request.trim()) {
      return;
    }

    try {
      setRunning(true);
      setError("");

      const data = await runAgent(
        Number(projectId),
        request.trim(),
      );

      console.log("Created agent run:", data);
      console.log("Created agent run JSON:", JSON.stringify(data, null, 2));

      const runId = (data as { run_id: number }).run_id;

      console.log("Created run ID:", runId);

      setRequest("");

      navigate(
        `/projects/${projectId}/runs/${runId}`,
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to start agent",
      );
    } finally {
      setRunning(false);
    }
  }

  async function handleDeleteProject() {
    if (!projectId || !project) {
      return;
    }

    const confirmed = window.confirm(
      `Delete "${project.name}"?\n\nThis will remove the project from Syntra.`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(true);
      setError("");

      await deleteProject(Number(projectId));

      navigate("/projects");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete project",
      );
      setDeleting(false);
    }
  }

  useEffect(() => {
    loadProject();
  }, [projectId]);

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-16 text-center">
          <Loader2
            size={26}
            className="mx-auto animate-spin text-zinc-500"
          />

          <p className="mt-3 text-sm text-zinc-500">
            Loading project...
          </p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center">
          <AlertCircle
            size={28}
            className="mx-auto text-red-400"
          />

          <h1 className="mt-4 text-lg font-medium text-white">
            Project not found
          </h1>

          <p className="mt-2 text-sm text-zinc-500">
            {error || "This project could not be loaded."}
          </p>

          <button
            type="button"
            onClick={() => navigate("/projects")}
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-medium text-black transition hover:bg-zinc-200"
          >
            <ArrowLeft size={15} />
            Back to Projects
          </button>
        </div>
      </div>
    );
  }

  const completedRuns = runs.filter(
    (run) =>
      run.status === "completed" ||
      run.status === "approved",
  ).length;

  const failedRuns = runs.filter(
    (run) => run.status === "failed",
  ).length;

  const runningRuns = runs.filter(
    (run) => run.status === "running",
  ).length;

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-5 py-8 sm:px-8">
      <div className="flex items-center justify-between gap-4">
        <button
          type="button"
          onClick={() => navigate("/projects")}
          className="inline-flex items-center gap-2 text-sm text-zinc-500 transition hover:text-white"
        >
          <ArrowLeft size={16} />
          Back to Projects
        </button>

        <button
          type="button"
          onClick={refreshProject}
          disabled={refreshing}
          className="inline-flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs font-medium text-zinc-400 transition hover:bg-zinc-800 hover:text-white disabled:opacity-50"
        >
          <RefreshCw
            size={14}
            className={refreshing ? "animate-spin" : ""}
          />
          Refresh
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <AlertCircle size={18} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-950">
                <GitBranch
                  size={20}
                  className="text-zinc-300"
                />
              </div>

              <div className="min-w-0">
                <h1 className="truncate text-2xl font-semibold text-white">
                  {project.name}
                </h1>

                <p className="mt-1 truncate text-sm text-zinc-500">
                  {project.repository_url}
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <a
              href={project.repository_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-zinc-800 hover:text-white"
            >
              GitHub
              <ExternalLink size={15} />
            </a>

            <button
              type="button"
              onClick={handleDeleteProject}
              disabled={deleting}
              className="inline-flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-sm font-medium text-red-400 transition hover:bg-red-500/15 disabled:opacity-50"
            >
              {deleting ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <Trash2 size={15} />
              )}
              Delete
            </button>
          </div>
        </div>

        <div className="mt-6 grid gap-3 border-t border-zinc-800 pt-6 sm:grid-cols-2 lg:grid-cols-4">
          <InfoItem
            label="Project ID"
            value={`#${project.id}`}
          />

          <InfoItem
            label="Total Runs"
            value={String(runs.length)}
          />

          <InfoItem
            label="Successful"
            value={String(completedRuns)}
          />

          <InfoItem
            label="Failed"
            value={String(failedRuns)}
          />
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
        <div>
          <h2 className="text-sm font-semibold text-white">
            Run Syntra
          </h2>

          <p className="mt-1 text-xs text-zinc-600">
            Describe the code change you want Syntra to make.
          </p>
        </div>

        <div className="mt-5">
          <textarea
            value={request}
            onChange={(event) => setRequest(event.target.value)}
            placeholder="Example: Add input validation to the registration form and create tests for invalid email addresses."
            rows={4}
            className="w-full resize-none rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm leading-6 text-white outline-none placeholder:text-zinc-700 transition focus:border-zinc-600"
          />

          <div className="mt-3 flex justify-end">
            <button
              type="button"
              onClick={handleRunAgent}
              disabled={running || !request.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-medium text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {running ? (
                <>
                  <Loader2
                    size={15}
                    className="animate-spin"
                  />
                  Starting...
                </>
              ) : (
                <>
                  <Play size={15} />
                  Run Agent
                </>
              )}
            </button>
          </div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          icon={<CheckCircle2 size={17} />}
          label="Successful Runs"
          value={completedRuns}
          className="text-emerald-400"
        />

        <StatCard
          icon={<XCircle size={17} />}
          label="Failed Runs"
          value={failedRuns}
          className="text-red-400"
        />

        <StatCard
          icon={<Activity size={17} />}
          label="Currently Running"
          value={runningRuns}
          className="text-yellow-400"
        />
      </div>

      <section>
        <div className="mb-4">
          <h2 className="text-sm font-semibold text-white">
            Recent Agent Runs
          </h2>

          <p className="mt-1 text-xs text-zinc-600">
            Review previous Syntra executions for this project.
          </p>
        </div>

        {runs.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/40 px-6 py-16 text-center">
            <Clock3
              size={28}
              className="mx-auto text-zinc-600"
            />

            <h3 className="mt-4 text-base font-medium text-white">
              No agent runs yet
            </h3>

            <p className="mt-2 text-sm text-zinc-500">
              Run Syntra above to create your first execution.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {runs.map((run) => (
              <Link
                key={run.id}
                to={`/projects/${project.id}/runs/${run.id}`}
                className="block rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 transition hover:border-zinc-700 hover:bg-zinc-900"
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="text-xs font-medium text-zinc-600">
                        RUN #{run.id}
                      </span>

                      <span
                        className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getStatusStyle(
                          run.status,
                        )}`}
                      >
                        {run.status}
                      </span>
                    </div>

                    <p className="mt-3 text-sm font-medium leading-6 text-zinc-200">
                      {run.user_request}
                    </p>

                    <p className="mt-2 text-xs text-zinc-600">
                      {formatDate(run.created_at)}
                    </p>
                  </div>

                  <div className="flex shrink-0 items-center gap-5 text-xs">
                    <div>
                      <p className="text-zinc-600">
                        Validation
                      </p>

                      <p
                        className={`mt-1 ${
                          run.validation_status === "passed"
                            ? "text-emerald-400"
                            : "text-zinc-400"
                        }`}
                      >
                        {run.validation_status ?? "—"}
                      </p>
                    </div>

                    <div>
                      <p className="text-zinc-600">
                        Tests
                      </p>

                      <p
                        className={`mt-1 ${
                          run.test_status === "passed"
                            ? "text-emerald-400"
                            : "text-zinc-400"
                        }`}
                      >
                        {run.test_status ?? "—"}
                      </p>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function InfoItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <p className="text-xs text-zinc-600">{label}</p>
      <p className="mt-1 text-sm text-zinc-300">{value}</p>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  className,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  className: string;
}) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5">
      <div className={`flex items-center gap-2 ${className}`}>
        {icon}
        <span className="text-xs">{label}</span>
      </div>

      <p className="mt-3 text-2xl font-semibold text-white">
        {value}
      </p>
    </div>
  );
}