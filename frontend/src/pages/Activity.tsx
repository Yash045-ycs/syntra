import {
  Activity as ActivityIcon,
  AlertCircle,
  CheckCircle2,
  Clock,
  GitCommit,
  GitPullRequest,
  Loader2,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getActivity } from "../services/api";

type ActivityLog = {
  id: number;
  project_id: number;
  agent_run_id: number | null;
  event_type: string;
  message: string;
  created_at: string;
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

function getEventIcon(eventType: string) {
  const type = eventType.toLowerCase();

  if (type.includes("pull") || type.includes("pr")) {
    return <GitPullRequest size={17} />;
  }

  if (type.includes("commit")) {
    return <GitCommit size={17} />;
  }

  if (
    type.includes("success") ||
    type.includes("passed") ||
    type.includes("completed")
  ) {
    return <CheckCircle2 size={17} />;
  }

  if (
    type.includes("failed") ||
    type.includes("error")
  ) {
    return <XCircle size={17} />;
  }

  if (
    type.includes("running") ||
    type.includes("started")
  ) {
    return <Loader2 size={17} />;
  }

  return <ActivityIcon size={17} />;
}

function getEventColor(eventType: string) {
  const type = eventType.toLowerCase();

  if (
    type.includes("success") ||
    type.includes("passed") ||
    type.includes("completed")
  ) {
    return "border-emerald-500/20 bg-emerald-500/10 text-emerald-400";
  }

  if (
    type.includes("failed") ||
    type.includes("error")
  ) {
    return "border-red-500/20 bg-red-500/10 text-red-400";
  }

  if (
    type.includes("pull") ||
    type.includes("pr")
  ) {
    return "border-purple-500/20 bg-purple-500/10 text-purple-400";
  }

  if (type.includes("commit")) {
    return "border-blue-500/20 bg-blue-500/10 text-blue-400";
  }

  return "border-zinc-700 bg-zinc-800/60 text-zinc-400";
}

function Activity() {
  const navigate = useNavigate();

  const [activities, setActivities] = useState<ActivityLog[]>([]);
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

      const data = (await getActivity()) as ActivityLog[];

      setActivities(data);
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

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-5 py-8 sm:px-8">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <ActivityIcon
              size={20}
              className="text-zinc-400"
            />

            <h1 className="text-3xl font-semibold text-white">
              Activity
            </h1>
          </div>

          <p className="mt-2 text-sm text-zinc-500">
            Track everything Syntra does across your projects.
          </p>
        </div>

        <button
          onClick={() => loadActivity(true)}
          disabled={loading || refreshing}
          className="flex items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-zinc-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw
            size={15}
            className={refreshing ? "animate-spin" : ""}
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
          <Clock
            size={30}
            className="mx-auto text-zinc-600"
          />

          <h2 className="mt-4 text-lg font-medium text-white">
            No activity yet
          </h2>

          <p className="mt-2 text-sm text-zinc-500">
            Syntra activity will appear here once an agent
            run starts.
          </p>
        </div>
      ) : (
        <div className="relative">
          <div className="absolute left-[19px] top-4 bottom-4 w-px bg-zinc-800" />

          <div className="space-y-5">
            {activities.map((activity) => (
              <div
                key={activity.id}
                className="relative flex gap-4"
              >
                <div
                  className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border ${getEventColor(
                    activity.event_type,
                  )}`}
                >
                  {getEventIcon(activity.event_type)}
                </div>

                <div className="min-w-0 flex-1 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 transition hover:border-zinc-700">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <p className="text-xs font-medium uppercase tracking-wider text-zinc-600">
                        {activity.event_type.replace(
                          /_/g,
                          " ",
                        )}
                      </p>

                      <p className="mt-2 text-sm leading-6 text-zinc-300">
                        {activity.message}
                      </p>
                    </div>

                    <span className="shrink-0 text-xs text-zinc-600">
                      {formatDate(activity.created_at)}
                    </span>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() =>
                        navigate(
                          `/projects/${activity.project_id}`,
                        )
                      }
                      className="rounded-lg border border-zinc-800 bg-zinc-950/50 px-2.5 py-1 text-xs text-zinc-500 transition hover:border-zinc-700 hover:text-zinc-300"
                    >
                      Project #{activity.project_id}
                    </button>

                    {activity.agent_run_id && (
                      <button
                        type="button"
                        onClick={() =>
                          navigate(
                            `/projects/${activity.project_id}/runs/${activity.agent_run_id}`,
                          )
                        }
                        className="rounded-lg border border-zinc-800 bg-zinc-950/50 px-2.5 py-1 text-xs text-zinc-500 transition hover:border-zinc-700 hover:text-zinc-300"
                      >
                        Run #{activity.agent_run_id}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Activity;