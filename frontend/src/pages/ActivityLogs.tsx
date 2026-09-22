import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  GitPullRequest,
  Loader2,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
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
  goal: string | null;
  pr_number: number | null;
  pr_url: string | null;
  validation_status: string | null;
  test_status: string | null;
  created_at: string;
  completed_at: string | null;
  error: string | null;
};

type ActivityEvent = {
  id: string;
  projectName: string;
  runId: number;
  title: string;
  description: string;
  time: string;
  icon: React.ElementType;
  iconClassName: string;
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

function formatDate(value: string) {
  const date = new Date(
    value.endsWith("Z") ? value : `${value}Z`,
  );

  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function Activity() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  async function loadActivity(isRefresh = false) {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const projectData = (await getProjects()) as Project[];

      setProjects(projectData);

      const allRuns: AgentRun[] = [];

      for (const project of projectData) {
        try {
          const projectRuns =
            (await getAgentRuns(project.id)) as AgentRun[];

          allRuns.push(...projectRuns);
        } catch {
          continue;
        }
      }

      allRuns.sort(
        (a, b) =>
          new Date(b.created_at).getTime() -
          new Date(a.created_at).getTime(),
      );

      setRuns(allRuns);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load activity",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadActivity();
  }, []);

  const activities = useMemo<ActivityEvent[]>(() => {
    const events: ActivityEvent[] = [];

    for (const run of runs) {
      const projectName =
        projects.find(
          (project) => project.id === run.project_id,
        )?.name ?? "Unknown Project";

      events.push({
        id: `started-${run.id}`,
        projectName,
        runId: run.id,
        title: "Agent run started",
        description: run.user_request,
        time: run.created_at,
        icon: Loader2,
        iconClassName: "text-yellow-400",
      });

      if (
        run.validation_status === "passed"
      ) {
        events.push({
          id: `validation-${run.id}`,
          projectName,
          runId: run.id,
          title: "Validation passed",
          description:
            "Syntra successfully validated the generated changes.",
          time: run.completed_at ?? run.created_at,
          icon: CheckCircle2,
          iconClassName: "text-emerald-400",
        });
      }

      if (
        run.test_status === "passed"
      ) {
        events.push({
          id: `tests-${run.id}`,
          projectName,
          runId: run.id,
          title: "Tests passed",
          description:
            "Repository tests completed successfully.",
          time: run.completed_at ?? run.created_at,
          icon: CheckCircle2,
          iconClassName: "text-emerald-400",
        });
      }

      if (run.pr_url) {
        events.push({
          id: `pr-${run.id}`,
          projectName,
          runId: run.id,
          title: "Pull request created",
          description: `PR #${run.pr_number}`,
          time: run.completed_at ?? run.created_at,
          icon: GitPullRequest,
          iconClassName: "text-blue-400",
        });
      }

      if (run.status === "failed") {
        events.push({
          id: `failed-${run.id}`,
          projectName,
          runId: run.id,
          title: "Agent run failed",
          description:
            run.error ||
            run.user_request,
          time: run.completed_at ?? run.created_at,
          icon: XCircle,
          iconClassName: "text-red-400",
        });
      }

      if (
        run.status === "completed" ||
        run.status === "approved"
      ) {
        events.push({
          id: `completed-${run.id}`,
          projectName,
          runId: run.id,
          title: "Agent run completed",
          description:
            "Syntra completed the requested change.",
          time: run.completed_at ?? run.created_at,
          icon: CheckCircle2,
          iconClassName: "text-emerald-400",
        });
      }
    }

    return events.sort(
      (a, b) =>
        new Date(b.time).getTime() -
        new Date(a.time).getTime(),
    );
  }, [projects, runs]);

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-5 py-8 sm:px-8">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-white">
            Activity
          </h1>

          <p className="mt-2 text-sm text-zinc-500">
            A chronological history of Syntra's agent activity.
          </p>
        </div>

        <button
          onClick={() => loadActivity(true)}
          disabled={loading || refreshing}
          className="flex items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-zinc-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw
            size={15}
            className={
              refreshing ? "animate-spin" : ""
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

      {loading ? (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-12 text-center">
          <Loader2
            size={24}
            className="mx-auto animate-spin text-zinc-500"
          />

          <p className="mt-3 text-sm text-zinc-500">
            Loading activity...
          </p>
        </div>
      ) : activities.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/40 px-6 py-16 text-center">
          <Clock3
            size={30}
            className="mx-auto text-zinc-600"
          />

          <h2 className="mt-4 text-lg font-medium text-white">
            No activity yet
          </h2>

          <p className="mt-2 text-sm text-zinc-500">
            Syntra activity will appear here after you run
            an agent.
          </p>
        </div>
      ) : (
        <div className="relative">
          <div className="absolute bottom-0 left-5 top-0 w-px bg-zinc-800" />

          <div className="space-y-1">
            {activities.map((activity) => {
              const Icon = activity.icon;

              return (
                <div
                  key={activity.id}
                  className="relative flex gap-5 rounded-xl px-2 py-5 transition hover:bg-white/[0.02]"
                >
                  <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-zinc-800 bg-zinc-950">
                    <Icon
                      size={14}
                      className={activity.iconClassName}
                    />
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                      <div className="text-sm font-medium text-zinc-200">
                        {activity.title}
                      </div>

                      <span className="text-[11px] text-zinc-600">
                        {formatRelativeTime(activity.time)}
                      </span>
                    </div>

                    <div className="mt-1 text-xs text-zinc-500">
                      {activity.projectName}
                      {" • "}
                      Run #{activity.runId}
                    </div>

                    <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
                      {activity.description}
                    </p>

                    <p className="mt-2 text-[10px] text-zinc-700">
                      {formatDate(activity.time)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default Activity;