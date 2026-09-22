import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  ExternalLink,
  GitBranch,
  GitCommit,
  Loader2,
  RefreshCw,
  ShieldCheck,
  TestTube2,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getAgentRuns, getProjects } from "../services/api";

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
  base_branch: string | null;
  agent_branch: string | null;
  base_commit_sha: string | null;
  agent_commit_sha: string | null;
  pr_number: number | null;
  pr_url: string | null;
  goal: string | null;
  validation_status: string | null;
  test_status: string | null;
  repair_iterations: number;
  error: string | null;
  created_at: string;
  completed_at: string | null;
};

function getStatusStyle(status: string) {
  switch (status.toLowerCase()) {
    case "approved":
      return {
        icon: CheckCircle2,
        className:
          "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
      };

    case "completed":
      return {
        icon: CheckCircle2,
        className: "border-blue-500/20 bg-blue-500/10 text-blue-400",
      };

    case "failed":
      return {
        icon: XCircle,
        className: "border-red-500/20 bg-red-500/10 text-red-400",
      };

    case "running":
      return {
        icon: Loader2,
        className: "border-yellow-500/20 bg-yellow-500/10 text-yellow-400",
      };

    default:
      return {
        icon: Clock3,
        className: "border-zinc-700 bg-zinc-800/60 text-zinc-400",
      };
  }
}

function formatDate(value: string) {
  const date = new Date(
    value.endsWith("Z") ? value : `${value}Z`,
  );

  return date.toLocaleString(undefined, {
    dateStyle: "short",
    timeStyle: "medium",
  });
}

function shortenCommit(value: string | null) {
  if (!value) {
    return "—";
  }

  return value.replace(/[\]\s]+$/, "").slice(0, 7);
}

function formatTestStatus(status: string | null) {
  if (status === "passed") {
    return {
      label: "Passed",
      className: "text-emerald-400",
    };
  }

  if (status === "failed") {
    return {
      label: "Failed",
      className: "text-red-400",
    };
  }

  if (status === "not_run" || status === "no_tests") {
    return {
      label: "Not Run",
      className: "text-zinc-400",
    };
  }

  return {
    label: "Not available",
    className: "text-zinc-400",
  };
}

export default function AgentRuns() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(
    null,
  );
  const [runs, setRuns] = useState<AgentRun[]>([]);

  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [error, setError] = useState("");

  async function loadProjects() {
    try {
      setLoadingProjects(true);
      setError("");

      const data = (await getProjects()) as Project[];

      setProjects(data);

      if (data.length > 0) {
        setSelectedProjectId((current) => current ?? data[0].id);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load projects",
      );
    } finally {
      setLoadingProjects(false);
    }
  }

  async function loadRuns(projectId: number) {
    try {
      setLoadingRuns(true);
      setError("");

      const data = (await getAgentRuns(projectId)) as AgentRun[];
      setRuns(data);
    } catch (err) {
      setRuns([]);
      setError(
        err instanceof Error ? err.message : "Failed to load agent runs",
      );
    } finally {
      setLoadingRuns(false);
    }
  }

  async function refreshRuns() {
    if (!selectedProjectId) {
      return;
    }

    await loadRuns(selectedProjectId);
  }

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadRuns(selectedProjectId);
    }
  }, [selectedProjectId]);

  const summary = useMemo(() => {
    return {
      total: runs.length,
      successful: runs.filter(
        (run) => run.status === "completed" || run.status === "approved",
      ).length,
      failed: runs.filter((run) => run.status === "failed").length,
      running: runs.filter((run) => run.status === "running").length,
    };
  }, [runs]);

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-5 py-8 sm:px-8">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-white">Agent Runs</h1>
          <p className="mt-2 text-sm text-zinc-500">
            Track Syntra's code changes, validation, tests, and pull requests.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <select
            value={selectedProjectId ?? ""}
            onChange={(event) =>
              setSelectedProjectId(
                event.target.value ? Number(event.target.value) : null,
              )
            }
            disabled={loadingProjects || projects.length === 0}
            className="min-w-64 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-2.5 text-sm text-white outline-none transition focus:border-zinc-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {projects.length === 0 ? (
              <option value="">No projects available</option>
            ) : (
              projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))
            )}
          </select>

          <button
            onClick={refreshRuns}
            disabled={loadingRuns || !selectedProjectId}
            className="flex items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-zinc-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw
              size={16}
              className={loadingRuns ? "animate-spin" : ""}
            />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <AlertCircle size={18} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5">
          <p className="text-sm text-zinc-500">Total Runs</p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {summary.total}
          </p>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5">
          <p className="text-sm text-zinc-500">Successful</p>
          <p className="mt-2 text-2xl font-semibold text-emerald-400">
            {summary.successful}
          </p>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5">
          <p className="text-sm text-zinc-500">Failed</p>
          <p className="mt-2 text-2xl font-semibold text-red-400">
            {summary.failed}
          </p>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5">
          <p className="text-sm text-zinc-500">Running</p>
          <p className="mt-2 text-2xl font-semibold text-yellow-400">
            {summary.running}
          </p>
        </div>
      </div>

      {loadingProjects || loadingRuns ? (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-12 text-center">
          <Loader2
            size={24}
            className="mx-auto animate-spin text-zinc-500"
          />
          <p className="mt-3 text-sm text-zinc-500">
            {loadingProjects
              ? "Loading projects..."
              : "Loading agent runs..."}
          </p>
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/40 px-6 py-16 text-center">
          <GitBranch size={28} className="mx-auto text-zinc-600" />
          <h2 className="mt-4 text-lg font-medium text-white">
            No projects yet
          </h2>
          <p className="mt-2 text-sm text-zinc-500">
            Add a GitHub repository to start running Syntra.
          </p>
        </div>
      ) : runs.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/40 px-6 py-16 text-center">
          <GitBranch size={28} className="mx-auto text-zinc-600" />
          <h2 className="mt-4 text-lg font-medium text-white">
            No agent runs yet
          </h2>
          <p className="mt-2 text-sm text-zinc-500">
            Run Syntra on this project and your executions will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-5">
          {runs.map((run) => {
            const status = getStatusStyle(run.status);
            const StatusIcon = status.icon;

            return (
              <Link
  key={run.id}
  to={`/projects/${run.project_id}/runs/${run.id}`}
  className="block rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 transition hover:border-zinc-700 hover:bg-zinc-900"
>
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="text-xs font-medium text-zinc-500">
                        RUN #{run.id}
                      </span>

                      <span
                        className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${status.className}`}
                      >
                        <StatusIcon
                          size={13}
                          className={
                            run.status === "running"
                              ? "animate-spin"
                              : ""
                          }
                        />
                        {run.status}
                      </span>
                    </div>

                    <h2 className="mt-4 text-base font-medium leading-6 text-white">
                      {run.user_request}
                    </h2>

                    <p className="mt-2 text-xs text-zinc-600">
                      Started {formatDate(run.created_at)}
                      {run.completed_at &&
                        ` • Completed ${formatDate(run.completed_at)}`}
                    </p>
                  </div>

                  {run.pr_url && (
                    <a
                      href={run.pr_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex shrink-0 items-center justify-center gap-2 rounded-xl border border-zinc-800 px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-zinc-800 hover:text-white"
                    >
                      Pull Request
                      <ExternalLink size={15} />
                    </a>
                  )}
                </div>

                {run.goal && (
                  <div className="mt-6 rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-zinc-600">
                      Agent Goal
                    </p>
                    <p className="mt-2 text-sm leading-6 text-zinc-300">
                      {run.goal}
                    </p>
                  </div>
                )}

                <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                    <div className="flex items-center gap-2 text-xs text-zinc-500">
                      <ShieldCheck size={15} />
                      Validation
                    </div>
                    <p
                      className={`mt-2 text-sm font-medium ${
                        run.validation_status === "passed"
                          ? "text-emerald-400"
                          : run.validation_status === "failed"
                            ? "text-red-400"
                            : "text-zinc-400"
                      }`}
                    >
                      {run.validation_status ?? "Not available"}
                    </p>
                  </div>

                  <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                    <div className="flex items-center gap-2 text-xs text-zinc-500">
                      <TestTube2 size={15} />
                      Tests
                    </div>
                    {(() => {
  const testStatus = formatTestStatus(run.test_status);

  return (
    <p
      className={`mt-2 text-sm font-medium ${testStatus.className}`}
    >
      {testStatus.label}
    </p>
  );
})()}
                  </div>

                  <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                    <div className="flex items-center gap-2 text-xs text-zinc-500">
                      <RefreshCw size={15} />
                      Repair Iterations
                    </div>
                    <p className="mt-2 text-sm font-medium text-white">
                      {run.repair_iterations}
                    </p>
                  </div>

                  <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                    <div className="flex items-center gap-2 text-xs text-zinc-500">
                      <GitCommit size={15} />
                      PR
                    </div>
                    <p className="mt-2 text-sm font-medium text-white">
                      {run.pr_number ? `#${run.pr_number}` : "Not created"}
                    </p>
                  </div>
                </div>

                {(run.base_branch ||
                  run.agent_branch ||
                  run.base_commit_sha ||
                  run.agent_commit_sha) && (
                  <div className="mt-5 grid gap-3 border-t border-zinc-800 pt-5 md:grid-cols-2">
                    <div>
                      <p className="text-xs text-zinc-600">Base</p>
                      <div className="mt-2 flex items-center gap-2 text-sm text-zinc-400">
                        <GitBranch size={14} />
                        <span>{run.base_branch ?? "—"}</span>
                        {run.base_commit_sha && (
                          <span className="font-mono text-xs text-zinc-600">
                            {shortenCommit(run.base_commit_sha)}
                          </span>
                        )}
                      </div>
                    </div>

                    <div>
                      <p className="text-xs text-zinc-600">Agent Branch</p>
                      <div className="mt-2 flex items-center gap-2 text-sm text-zinc-400">
                        <GitBranch size={14} />
                        <span className="truncate">
                          {run.agent_branch ?? "—"}
                        </span>
                        {run.agent_commit_sha && (
                          <span className="shrink-0 font-mono text-xs text-zinc-600">
                            {shortenCommit(run.agent_commit_sha)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {run.error && (
                  <div className="mt-5 rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                    <div className="flex items-center gap-2 text-xs font-medium text-red-400">
                      <AlertCircle size={15} />
                      Error
                    </div>
                    <p className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap text-xs leading-5 text-red-300/80">
                      {run.error}
                    </p>
                  </div>
                )}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}