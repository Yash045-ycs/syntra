import { useEffect, useState } from "react";
import {
  Code2,
  CheckCircle2,
  ExternalLink,
  Loader2,
  AlertCircle,
} from "lucide-react";
import {
  getCurrentUser,
  getGitHubAuthorizationUrl,
} from "../services/api";

type User = {
  id: number;
  email: string;
  github_username?: string | null;
};

function GitHubPage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connected = params.get("connected");
    const errorCode = params.get("error");

    if (connected === "true") {
      setSuccess(true);
    }

    if (errorCode) {
      setError(getGitHubErrorMessage(errorCode));
    }

    if (connected === "true" || errorCode) {
      window.history.replaceState({}, "", "/github");
    }

    loadUser();
  }, []);

  async function loadUser() {
    try {
      setLoading(true);

      const data = (await getCurrentUser()) as User;
      setUser(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load GitHub connection status",
      );
    } finally {
      setLoading(false);
    }
  }

  async function connectGitHub() {
    try {
      setConnecting(true);
      setError("");
      setSuccess(false);

      const data = await getGitHubAuthorizationUrl();

      window.location.href = data.authorization_url;
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to connect GitHub",
      );
      setConnecting(false);
    }
  }

  function getGitHubErrorMessage(errorCode: string) {
    switch (errorCode) {
      case "github_already_linked":
        return "This GitHub account is already connected to another Syntra account.";

      case "invalid_state":
        return "The GitHub connection session expired or is invalid. Please try again.";

      case "user_not_found":
        return "The Syntra account associated with this connection could not be found.";

      case "account_not_linked":
        return "This GitHub account is not linked to a Syntra account.";

      case "github_authorization_failed":
        return "GitHub authorization failed. Please try connecting again.";

      default:
        return "Unable to connect your GitHub account. Please try again.";
    }
  }

  const isConnected = Boolean(user?.github_username);

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      <div>
        <h1 className="text-2xl font-semibold text-white">
          GitHub
        </h1>

        <p className="mt-2 text-sm text-zinc-500">
          Connect your GitHub account to manage your repositories
          securely with Syntra.
        </p>
      </div>

      {success && (
        <div className="mt-6 flex items-start gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3">
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />

          <div>
            <p className="text-sm font-medium text-emerald-400">
              GitHub connected successfully
            </p>

            <p className="mt-1 text-sm text-emerald-400/70">
              Your GitHub account is now connected to Syntra.
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-6 flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />

          <div>
            <p className="text-sm font-medium text-red-400">
              GitHub connection failed
            </p>

            <p className="mt-1 text-sm text-red-400/70">
              {error}
            </p>
          </div>
        </div>
      )}

      <div className="mt-8 max-w-3xl">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900">
              <Code2 className="h-6 w-6 text-white" />
            </div>

            <div className="flex-1">
              <h2 className="text-base font-medium text-white">
                GitHub Account
              </h2>

              <p className="mt-1 text-sm leading-6 text-zinc-500">
                Syntra uses your GitHub connection to verify repository
                ownership and perform authorized Git operations.
              </p>
            </div>
          </div>

          {loading ? (
            <div className="mt-6 flex items-center gap-2 text-sm text-zinc-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Checking GitHub connection...
            </div>
          ) : isConnected ? (
            <div className="mt-6 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-400" />

                <div>
                  <p className="text-sm font-medium text-emerald-400">
                    GitHub Connected
                  </p>

                  <p className="mt-1 text-sm text-zinc-400">
                    Connected as{" "}
                    <span className="font-medium text-white">
                      @{user?.github_username}
                    </span>
                  </p>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-3">
                <a
                  href={`https://github.com/${user?.github_username}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-medium text-zinc-200 transition hover:border-zinc-600 hover:bg-zinc-800"
                >
                  View GitHub Profile
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            </div>
          ) : (
            <div className="mt-6">
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
                <p className="text-sm font-medium text-white">
                  GitHub is not connected
                </p>

                <p className="mt-1 text-sm leading-6 text-zinc-500">
                  Connect your GitHub account before adding repositories
                  to Syntra. This allows Syntra to verify that the
                  repositories belong to your GitHub account.
                </p>
              </div>

              <button
                type="button"
                onClick={connectGitHub}
                disabled={connecting}
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-medium text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {connecting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Code2 className="h-4 w-4" />
                    Connect GitHub
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default GitHubPage;