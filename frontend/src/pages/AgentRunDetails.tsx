import {
  AlertCircle,
  ArrowLeft,
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
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  approveAgentRun,
  getAgentRun,
  getAgentRunPrStatus,
  getProject,
  getRunDiff,
  mergeAgentRun,
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

type PullRequestStatus = {
  number: number;
  title: string;
  url: string;
  state: string;
  merged: boolean;
  mergeable: boolean | null;
  draft: boolean;
  head: string;
  base: string;
};

type PullRequestResponse = {
  run_id: number;
  database_status: string;
  pull_request: PullRequestStatus;
};

type RunDiffFile = {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  changes: number;
  patch: string | null;
};

type RunDiff = {
  run_id: number;
  pr_number: number;
  files: RunDiffFile[];
  summary: {
    files_changed: number;
    additions: number;
    deletions: number;
  };
};

function formatDate(value: string | null) {
  if (!value) {
    return "—";
  }

  const date = new Date(
    value.endsWith("Z") ? value : `${value}Z`,
  );

  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  });
}

function shortenCommit(value: string | null) {
  if (!value) {
    return "—";
  }

  return value
    .replace(/[\]\s]+$/, "")
    .slice(0, 7);
}

function getStatusStyle(status: string) {
  switch (status.toLowerCase()) {
    case "approved":
      return {
        icon: CheckCircle2,
        className:
          "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
      };

    case "merged":
      return {
        icon: CheckCircle2,
        className:
          "border-purple-500/20 bg-purple-500/10 text-purple-400",
      };

    case "completed":
      return {
        icon: CheckCircle2,
        className:
          "border-blue-500/20 bg-blue-500/10 text-blue-400",
      };

    case "failed":
      return {
        icon: XCircle,
        className:
          "border-red-500/20 bg-red-500/10 text-red-400",
      };

    case "running":
      return {
        icon: Loader2,
        className:
          "border-yellow-500/20 bg-yellow-500/10 text-yellow-400",
      };

    default:
      return {
        icon: Clock3,
        className:
          "border-zinc-700 bg-zinc-800/60 text-zinc-400",
      };
  }
}

function statusTextClass(status: string | null) {
  if (status === "passed") {
    return "text-emerald-400";
  }

  if (status === "failed") {
    return "text-red-400";
  }

  return "text-zinc-400";
}

function StatusCard({
  icon,
  label,
  value,
  className,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  className: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        {icon}
        {label}
      </div>

      <p
        className={`mt-2 text-sm font-medium ${className}`}
      >
        {value}
      </p>
    </div>
  );
}

export default function AgentRunDetails() {
  const { projectId, runId } = useParams<{
    projectId: string;
    runId: string;
  }>();

  const navigate = useNavigate();

  const parsedProjectId = Number(projectId);
  const parsedRunId = Number(runId);

  const validParams =
    Number.isInteger(parsedProjectId) &&
    parsedProjectId > 0 &&
    Number.isInteger(parsedRunId) &&
    parsedRunId > 0;

  const [run, setRun] =
    useState<AgentRun | null>(null);

  const [project, setProject] =
    useState<Project | null>(null);

  const [diff, setDiff] =
    useState<RunDiff | null>(null);

  const [prStatus, setPrStatus] =
    useState<PullRequestResponse | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [loadingDiff, setLoadingDiff] =
    useState(false);

  const [loadingPrStatus, setLoadingPrStatus] =
    useState(false);

  const [approving, setApproving] =
    useState(false);

  const [merging, setMerging] =
    useState(false);

  const [error, setError] =
    useState("");

  async function loadRun() {
    if (!validParams) {
      setError(
        "Invalid project or agent run ID.",
      );
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");

      const [runData, projectData] =
        await Promise.all([
          getAgentRun(
            parsedProjectId,
            parsedRunId,
          ),
          getProject(parsedProjectId),
        ]);

      setRun(runData as AgentRun);
      setProject(projectData as Project);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load agent run",
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadDiff() {
    if (!validParams) {
      return;
    }

    try {
      setLoadingDiff(true);
      setError("");

      const data = await getRunDiff(
        parsedProjectId,
        parsedRunId,
      );

      setDiff(data as RunDiff);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load run diff",
      );
    } finally {
      setLoadingDiff(false);
    }
  }

  async function loadPrStatus() {
    if (!validParams) {
      return;
    }

    try {
      setLoadingPrStatus(true);

      const data =
        await getAgentRunPrStatus(
          parsedProjectId,
          parsedRunId,
        );

      setPrStatus(
        data as PullRequestResponse,
      );
    } catch (err) {
      setPrStatus(null);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to load pull request status",
      );
    } finally {
      setLoadingPrStatus(false);
    }
  }

  async function handleApprove() {
    if (!validParams) {
      return;
    }

    try {
      setApproving(true);
      setError("");

      await approveAgentRun(
        parsedProjectId,
        parsedRunId,
      );

      await loadRun();
      await loadPrStatus();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to approve agent run",
      );
    } finally {
      setApproving(false);
    }
  }

  async function handleMerge() {
    if (!validParams) {
      return;
    }

    try {
      setMerging(true);
      setError("");

      await mergeAgentRun(
        parsedProjectId,
        parsedRunId,
      );

      await loadRun();
      await loadPrStatus();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to merge pull request",
      );
    } finally {
      setMerging(false);
    }
  }

  useEffect(() => {
    if (!validParams) {
      setError(
        "Invalid project or agent run ID.",
      );
      setLoading(false);
      return;
    }

    loadRun();
  }, [projectId, runId]);

  useEffect(() => {
    if (
      validParams &&
      run?.pr_number
    ) {
      loadPrStatus();
    }
  }, [
    validParams,
    run?.pr_number,
    run?.status,
  ]);

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-16 text-center">
          <Loader2
            size={26}
            className="mx-auto animate-spin text-zinc-500"
          />

          <p className="mt-3 text-sm text-zinc-500">
            Loading agent run...
          </p>
        </div>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center">
          <AlertCircle
            size={28}
            className="mx-auto text-red-400"
          />

          <h1 className="mt-4 text-lg font-medium text-white">
            Agent run not found
          </h1>

          <p className="mt-2 text-sm text-zinc-500">
            {error ||
              "This agent run could not be loaded."}
          </p>

          <button
            type="button"
            onClick={() =>
              navigate("/runs")
            }
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-medium text-black transition hover:bg-zinc-200"
          >
            <ArrowLeft size={15} />
            Back to Agent Runs
          </button>
        </div>
      </div>
    );
  }

  const status =
    getStatusStyle(run.status);

  const StatusIcon = status.icon;

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-5 py-8 sm:px-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={() =>
            navigate("/runs")
          }
          className="inline-flex w-fit items-center gap-2 text-sm text-zinc-500 transition hover:text-white"
        >
          <ArrowLeft size={16} />
          Back to Agent Runs
        </button>

        <button
          type="button"
          onClick={loadRun}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs font-medium text-zinc-400 transition hover:bg-zinc-800 hover:text-white disabled:opacity-50"
        >
          <RefreshCw
            size={14}
            className={
              loading
                ? "animate-spin"
                : ""
            }
          />
          Refresh
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <AlertCircle
            size={18}
            className="mt-0.5 shrink-0"
          />

          <span>{error}</span>
        </div>
      )}

      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs font-medium text-zinc-600">
                RUN #{run.id}
              </span>

              <span
                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${status.className}`}
              >
                <StatusIcon
                  size={13}
                  className={
                    run.status ===
                    "running"
                      ? "animate-spin"
                      : ""
                  }
                />

                {run.status}
              </span>
            </div>

            <h1 className="mt-4 text-2xl font-semibold text-white">
              {run.user_request}
            </h1>

            {project && (
              <Link
                to={`/projects/${project.id}`}
                className="mt-2 inline-flex items-center gap-2 text-sm text-zinc-500 transition hover:text-white"
              >
                <GitBranch size={14} />
                {project.name}
              </Link>
            )}
          </div>

          {run.pr_url && (
            <a
              href={run.pr_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-zinc-800 hover:text-white"
            >
              Open Pull Request
              <ExternalLink size={15} />
            </a>
          )}
        </div>

        <div className="mt-6 grid gap-3 border-t border-zinc-800 pt-6 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-xs text-zinc-600">
              Started
            </p>

            <p className="mt-1 text-sm text-zinc-300">
              {formatDate(
                run.created_at,
              )}
            </p>
          </div>

          <div>
            <p className="text-xs text-zinc-600">
              Completed
            </p>

            <p className="mt-1 text-sm text-zinc-300">
              {formatDate(
                run.completed_at,
              )}
            </p>
          </div>

          <div>
            <p className="text-xs text-zinc-600">
              Pull Request
            </p>

            <p className="mt-1 text-sm text-zinc-300">
              {run.pr_number
                ? `#${run.pr_number}`
                : "Not created"}
            </p>
          </div>

          <div>
            <p className="text-xs text-zinc-600">
              Repair Iterations
            </p>

            <p className="mt-1 text-sm text-zinc-300">
              {run.repair_iterations}
            </p>
          </div>
        </div>
      </div>

      {run.pr_number && (
        <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-white">
                Pull Request
              </h2>

              <p className="mt-1 text-xs text-zinc-600">
                Live status from GitHub.
              </p>
            </div>

            <button
              type="button"
              onClick={
                loadPrStatus
              }
              disabled={
                loadingPrStatus
              }
              className="inline-flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs font-medium text-zinc-400 transition hover:bg-zinc-800 hover:text-white disabled:opacity-50"
            >
              <RefreshCw
                size={14}
                className={
                  loadingPrStatus
                    ? "animate-spin"
                    : ""
                }
              />

              Refresh PR
            </button>
          </div>

          {loadingPrStatus &&
          !prStatus ? (
            <div className="mt-6 flex items-center gap-2 text-sm text-zinc-500">
              <Loader2
                size={16}
                className="animate-spin"
              />

              Loading pull request status...
            </div>
          ) : prStatus ? (
            <div className="mt-5 space-y-5">
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-lg font-semibold text-white">
                  PR #
                  {
                    prStatus
                      .pull_request
                      .number
                  }
                </span>

                <span
                  className={`rounded-full border px-2.5 py-1 text-xs font-medium ${
                    prStatus
                      .pull_request
                      .merged
                      ? "border-purple-500/20 bg-purple-500/10 text-purple-400"
                      : prStatus
                            .pull_request
                            .state ===
                          "open"
                        ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                        : "border-zinc-700 bg-zinc-800/60 text-zinc-400"
                  }`}
                >
                  {prStatus
                    .pull_request
                    .merged
                    ? "Merged"
                    : prStatus
                        .pull_request
                        .state}
                </span>

                {prStatus
                  .pull_request
                  .draft && (
                  <span className="rounded-full border border-yellow-500/20 bg-yellow-500/10 px-2.5 py-1 text-xs font-medium text-yellow-400">
                    Draft
                  </span>
                )}
              </div>

              <p className="text-sm text-zinc-300">
                {
                  prStatus
                    .pull_request
                    .title
                }
              </p>

              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <StatusCard
                  icon={
                    <GitBranch
                      size={17}
                    />
                  }
                  label="State"
                  value={
                    prStatus
                      .pull_request
                      .merged
                      ? "Merged"
                      : prStatus
                          .pull_request
                          .state
                  }
                  className="text-white"
                />

                <StatusCard
                  icon={
                    <CheckCircle2
                      size={17}
                    />
                  }
                  label="Merged"
                  value={
                    prStatus
                      .pull_request
                      .merged
                      ? "Yes"
                      : "No"
                  }
                  className={
                    prStatus
                      .pull_request
                      .merged
                      ? "text-purple-400"
                      : "text-zinc-400"
                  }
                />

                <StatusCard
                  icon={
                    <ShieldCheck
                      size={17}
                    />
                  }
                  label="Mergeable"
                  value={
                    prStatus
                      .pull_request
                      .mergeable ===
                    null
                      ? "Unknown"
                      : prStatus
                          .pull_request
                          .mergeable
                        ? "Yes"
                        : "No"
                  }
                  className={
                    prStatus
                      .pull_request
                      .mergeable ===
                    true
                      ? "text-emerald-400"
                      : prStatus
                          .pull_request
                          .mergeable ===
                        false
                        ? "text-red-400"
                        : "text-zinc-400"
                  }
                />

                <StatusCard
                  icon={
                    <GitBranch
                      size={17}
                    />
                  }
                  label="Branches"
                  value={`${prStatus.pull_request.head} → ${prStatus.pull_request.base}`}
                  className="text-zinc-300"
                />
              </div>

              <div>
                <a
                  href={
                    prStatus
                      .pull_request
                      .url
                  }
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-zinc-800 hover:text-white"
                >
                  Open Pull Request
                  <ExternalLink
                    size={15}
                  />
                </a>
              </div>
            </div>
          ) : (
            <p className="mt-5 text-sm text-zinc-600">
              Pull request status is not available.
            </p>
          )}
        </section>
      )}

      {run.goal && (
        <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
          <h2 className="text-sm font-semibold text-white">
            Agent Goal
          </h2>

          <p className="mt-3 text-sm leading-7 text-zinc-400">
            {run.goal}
          </p>
        </section>
      )}

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
        <h2 className="text-sm font-semibold text-white">
          Execution Status
        </h2>

        <div className="mt-5 grid gap-3 md:grid-cols-3">
          <StatusCard
            icon={
              <ShieldCheck
                size={17}
              />
            }
            label="Validation"
            value={
              run.validation_status ??
              "Not available"
            }
            className={statusTextClass(
              run.validation_status,
            )}
          />

          <StatusCard
            icon={
              <TestTube2
                size={17}
              />
            }
            label="Tests"
            value={
              run.test_status ??
              "Not available"
            }
            className={statusTextClass(
              run.test_status,
            )}
          />

          <StatusCard
            icon={
              <RefreshCw
                size={17}
              />
            }
            label="Repair Iterations"
            value={String(
              run.repair_iterations,
            )}
            className="text-white"
          />
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
        <h2 className="text-sm font-semibold text-white">
          Git Changes
        </h2>

        <div className="mt-5 grid gap-5 md:grid-cols-2">
          <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
            <div className="flex items-center gap-2 text-xs text-zinc-500">
              <GitBranch
                size={15}
              />
              Base Branch
            </div>

            <p className="mt-2 text-sm text-zinc-300">
              {run.base_branch ??
                "—"}
            </p>

            {run.base_commit_sha && (
              <p className="mt-2 font-mono text-xs text-zinc-600">
                {shortenCommit(
                  run.base_commit_sha,
                )}
              </p>
            )}
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
            <div className="flex items-center gap-2 text-xs text-zinc-500">
              <GitBranch
                size={15}
              />
              Agent Branch
            </div>

            <p className="mt-2 break-all text-sm text-zinc-300">
              {run.agent_branch ??
                "—"}
            </p>

            {run.agent_commit_sha && (
              <p className="mt-2 font-mono text-xs text-zinc-600">
                {shortenCommit(
                  run.agent_commit_sha,
                )}
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">
              Code Diff
            </h2>

            <p className="mt-1 text-xs text-zinc-600">
              Review the changes generated by Syntra.
            </p>
          </div>

          <button
            type="button"
            onClick={loadDiff}
            disabled={loadingDiff}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs font-medium text-zinc-400 transition hover:bg-zinc-800 hover:text-white disabled:opacity-50"
          >
            {loadingDiff ? (
              <Loader2
                size={14}
                className="animate-spin"
              />
            ) : (
              <GitCommit
                size={14}
              />
            )}

            {diff === null
              ? "Load Diff"
              : "Reload Diff"}
          </button>
        </div>

        {diff !== null && (
          <div className="mt-5 space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                <p className="text-xs text-zinc-600">
                  Files Changed
                </p>

                <p className="mt-1 text-lg font-semibold text-white">
                  {
                    diff.summary
                      .files_changed
                  }
                </p>
              </div>

              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                <p className="text-xs text-zinc-600">
                  Additions
                </p>

                <p className="mt-1 text-lg font-semibold text-emerald-400">
                  +
                  {
                    diff.summary
                      .additions
                  }
                </p>
              </div>

              <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                <p className="text-xs text-zinc-600">
                  Deletions
                </p>

                <p className="mt-1 text-lg font-semibold text-red-400">
                  -
                  {
                    diff.summary
                      .deletions
                  }
                </p>
              </div>
            </div>

            {diff.files.length ===
            0 ? (
              <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-950/40 p-8 text-center">
                <p className="text-sm text-zinc-500">
                  No file changes found in this pull request.
                </p>
              </div>
            ) : (
              diff.files.map(
                (file) => (
                  <div
                    key={
                      file.filename
                    }
                    className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950/40"
                  >
                    <div className="flex flex-col gap-3 border-b border-zinc-800 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                      <div className="min-w-0">
                        <p className="break-all font-mono text-sm text-zinc-300">
                          {
                            file.filename
                          }
                        </p>

                        <p className="mt-1 text-xs text-zinc-600">
                          {
                            file.status
                          }
                        </p>
                      </div>

                      <div className="flex shrink-0 items-center gap-3 text-xs">
                        <span className="text-emerald-400">
                          +
                          {
                            file.additions
                          }
                        </span>

                        <span className="text-red-400">
                          -
                          {
                            file.deletions
                          }
                        </span>

                        <span className="text-zinc-600">
                          {
                            file.changes
                          }{" "}
                          changes
                        </span>
                      </div>
                    </div>

                    {file.patch ? (
                      <pre className="max-h-[500px] overflow-auto bg-[#09090b] p-4 font-mono text-xs leading-6">
                        {file.patch
                          .split("\n")
                          .map(
                            (
                              line,
                              index,
                            ) => {
                              let className =
                                "text-zinc-500";

                              if (
                                line.startsWith(
                                  "+",
                                )
                              ) {
                                className =
                                  "bg-emerald-500/10 text-emerald-400";
                              } else if (
                                line.startsWith(
                                  "-",
                                )
                              ) {
                                className =
                                  "bg-red-500/10 text-red-400";
                              } else if (
                                line.startsWith(
                                  "@@",
                                )
                              ) {
                                className =
                                  "bg-blue-500/10 text-blue-400";
                              }

                              return (
                                <div
                                  key={
                                    index
                                  }
                                  className={`whitespace-pre ${className}`}
                                >
                                  {
                                    line
                                  }
                                </div>
                              );
                            },
                          )}
                      </pre>
                    ) : (
                      <div className="px-4 py-6 text-center text-xs text-zinc-600">
                        No patch data available for this file.
                      </div>
                    )}
                  </div>
                ),
              )
            )}
          </div>
        )}
      </section>

      {run.error && (
        <section className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6">
          <div className="flex items-center gap-2 text-sm font-medium text-red-400">
            <AlertCircle
              size={17}
            />
            Agent Error
          </div>

          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-red-300/80">
            {run.error}
          </p>
        </section>
      )}

      {run.status ===
        "completed" && (
        <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-white">
                Review & Approval
              </h2>

              <p className="mt-1 text-xs text-zinc-600">
                Approve this agent run after reviewing the generated changes.
              </p>
            </div>

            <button
              type="button"
              onClick={
                handleApprove
              }
              disabled={approving}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-medium text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {approving ? (
                <>
                  <Loader2
                    size={15}
                    className="animate-spin"
                  />
                  Approving...
                </>
              ) : (
                <>
                  <CheckCircle2
                    size={15}
                  />
                  Approve Run
                </>
              )}
            </button>
          </div>
        </section>
      )}

      {run.status ===
        "approved" && (
        <section className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle2
                size={20}
                className="text-emerald-400"
              />

              <div>
                <h2 className="text-sm font-semibold text-emerald-400">
                  Agent Run Approved
                </h2>

                <p className="mt-1 text-xs text-emerald-400/70">
                  The generated changes are approved and ready to merge.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={
                handleMerge
              }
              disabled={merging}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-medium text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {merging ? (
                <>
                  <Loader2
                    size={15}
                    className="animate-spin"
                  />
                  Merging...
                </>
              ) : (
                <>
                  <GitCommit
                    size={15}
                  />
                  Merge Pull Request
                </>
              )}
            </button>
          </div>
        </section>
      )}

      {run.status ===
        "merged" && (
        <section className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6">
          <div className="flex items-center gap-3">
            <CheckCircle2
              size={20}
              className="text-emerald-400"
            />

            <div>
              <h2 className="text-sm font-semibold text-emerald-400">
                Pull Request Merged
              </h2>

              <p className="mt-1 text-xs text-emerald-400/70">
                Syntra successfully merged the generated changes into the base branch.
              </p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}