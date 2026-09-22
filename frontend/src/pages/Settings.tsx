import {
  Bell,
  CheckCircle2,
  ExternalLink,
  GitBranch,
  LogIn,
  LogOut,
  ShieldCheck,
  User,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCurrentUser } from "../services/api";

type UserData = {
  id: number;
  email: string;
  github_username?: string | null;
};

function Settings() {
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [saved, setSaved] = useState(false);

  const [user, setUser] = useState<UserData | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);

  useEffect(() => {
    const storedNotifications =
      localStorage.getItem("syntra-notifications");

    if (storedNotifications !== null) {
      setNotifications(storedNotifications === "true");
    }

    const storedAutoRefresh =
      localStorage.getItem("syntra-auto-refresh");

    if (storedAutoRefresh !== null) {
      setAutoRefresh(storedAutoRefresh === "true");
    }

    loadUser();
  }, []);

  async function loadUser() {
    const token = localStorage.getItem("syntra_token");

    if (!token) {
      setLoadingUser(false);
      return;
    }

    try {
      const data = (await getCurrentUser()) as UserData;
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setLoadingUser(false);
    }
  }

  function handleNotificationsChange(value: boolean) {
    setNotifications(value);

    localStorage.setItem(
      "syntra-notifications",
      String(value),
    );

    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  function handleAutoRefreshChange(value: boolean) {
    setAutoRefresh(value);

    localStorage.setItem(
      "syntra-auto-refresh",
      String(value),
    );

    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  function handleLogin() {
    navigate("/login");
  }

  function handleLogout() {
    localStorage.removeItem("syntra_token");
    navigate("/login");
  }

  const isLoggedIn = Boolean(localStorage.getItem("syntra_token"));

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-5 py-8 sm:px-8">
      <div>
        <h1 className="text-3xl font-semibold text-white">
          Settings
        </h1>

        <p className="mt-2 text-sm text-zinc-500">
          Manage your Syntra account and workspace preferences.
        </p>
      </div>

      {saved && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400">
          <CheckCircle2 size={16} />
          Settings saved
        </div>
      )}

      <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950">
        <div className="border-b border-zinc-800 px-6 py-5">
          <div className="flex items-center gap-3">
            <User size={18} className="text-zinc-400" />

            <div>
              <h2 className="text-sm font-semibold text-white">
                Account
              </h2>

              <p className="mt-1 text-xs text-zinc-600">
                Manage your Syntra account.
              </p>
            </div>
          </div>
        </div>

        <div className="px-6 py-5">
          {loadingUser ? (
            <div className="text-sm text-zinc-500">
              Loading account details...
            </div>
          ) : isLoggedIn && user ? (
            <div>
              <div className="flex items-start justify-between gap-5">
                <div className="flex items-center gap-4">
                  <div className="flex h-11 w-11 items-center justify-center rounded-full border border-zinc-700 bg-zinc-900 text-sm font-semibold text-white">
                    {user.email.charAt(0).toUpperCase()}
                  </div>

                  <div>
                    <p className="text-sm font-medium text-white">
                      {user.email}
                    </p>

                    <p className="mt-1 text-xs text-zinc-600">
                      Syntra account #{user.id}
                    </p>
                  </div>
                </div>

                <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-2.5 py-1 text-[10px] text-emerald-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  Logged in
                </span>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
                  <p className="text-[10px] uppercase tracking-[0.14em] text-zinc-600">
                    Email
                  </p>

                  <p className="mt-2 truncate text-sm text-zinc-300">
                    {user.email}
                  </p>
                </div>

                <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
                  <p className="text-[10px] uppercase tracking-[0.14em] text-zinc-600">
                    GitHub
                  </p>

                  <p className="mt-2 text-sm text-zinc-300">
                    {user.github_username
                      ? `@${user.github_username}`
                      : "Not connected"}
                  </p>
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="inline-flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-sm font-medium text-red-400 transition hover:border-red-500/30 hover:bg-red-500/15"
                >
                  <LogOut size={15} />
                  Log out
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900">
                    <User size={18} className="text-zinc-400" />
                  </div>

                  <div>
                    <p className="text-sm font-medium text-white">
                      You are not logged in
                    </p>

                    <p className="mt-1 text-xs leading-5 text-zinc-600">
                      Log in to access your Syntra account, projects,
                      agent runs, and GitHub-connected features.
                    </p>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={handleLogin}
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-medium text-black transition hover:bg-zinc-200"
              >
                <LogIn size={15} />
                Log in
              </button>
            </div>
          )}
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950">
        <div className="border-b border-zinc-800 px-6 py-5">
          <div className="flex items-center gap-3">
            <Bell size={18} className="text-zinc-400" />

            <div>
              <h2 className="text-sm font-semibold text-white">
                Notifications
              </h2>

              <p className="mt-1 text-xs text-zinc-600">
                Control how Syntra reports agent activity.
              </p>
            </div>
          </div>
        </div>

        <div className="divide-y divide-zinc-800">
          <SettingRow
            title="Agent run notifications"
            description="Show notifications when agent runs complete or fail."
            enabled={notifications}
            onChange={handleNotificationsChange}
          />

          <SettingRow
            title="Automatic run refresh"
            description="Keep agent run information updated automatically."
            enabled={autoRefresh}
            onChange={handleAutoRefreshChange}
          />
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950">
        <div className="border-b border-zinc-800 px-6 py-5">
          <div className="flex items-center gap-3">
            <ShieldCheck size={18} className="text-zinc-400" />

            <div>
              <h2 className="text-sm font-semibold text-white">
                Security
              </h2>

              <p className="mt-1 text-xs text-zinc-600">
                GitHub and repository access.
              </p>
            </div>
          </div>
        </div>

        <div className="px-6 py-5">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900">
              <GitBranch size={18} className="text-zinc-300" />
            </div>

            <div className="flex-1">
              <p className="text-sm font-medium text-white">
                GitHub access
              </p>

              <p className="mt-1 text-xs leading-5 text-zinc-600">
                Manage your GitHub connection and repository
                permissions from the GitHub page.
              </p>

              <button
                type="button"
                onClick={() => navigate("/github")}
                className="mt-4 inline-flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-2 text-xs font-medium text-zinc-300 transition hover:border-zinc-700 hover:bg-zinc-800 hover:text-white"
              >
                Manage GitHub
                <ExternalLink size={13} />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function SettingRow({
  title,
  description,
  enabled,
  onChange,
}: {
  title: string;
  description: string;
  enabled: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-5 px-6 py-5">
      <div>
        <p className="text-sm font-medium text-zinc-300">
          {title}
        </p>

        <p className="mt-1 text-xs leading-5 text-zinc-600">
          {description}
        </p>
      </div>

      <button
        type="button"
        onClick={() => onChange(!enabled)}
        className={`relative h-6 w-11 shrink-0 rounded-full transition ${
          enabled ? "bg-white" : "bg-zinc-800"
        }`}
        aria-label={`Toggle ${title}`}
      >
        <span
          className={`absolute top-1 h-4 w-4 rounded-full transition ${
            enabled
              ? "left-6 bg-black"
              : "left-1 bg-zinc-500"
          }`}
        />
      </button>
    </div>
  );
}

export default Settings;
