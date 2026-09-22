import {
  ExternalLink,
  FolderGit2,
  Plus,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createProject,
  deleteProject,
  getGitHubRepositories,
  getProjects,
} from "../services/api";

type Project = {
  id: number;
  name: string;
  repository_url: string;
  owner_id: number;
};

type GitHubRepository = {
  id: number;
  name: string;
  full_name: string;
  owner: string;
  private: boolean;
  html_url: string;
  default_branch: string;
};

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);

  const [repositories, setRepositories] = useState<GitHubRepository[]>([]);
  const [loadingRepositories, setLoadingRepositories] = useState(false);

  const [name, setName] = useState("");
  const [repositoryUrl, setRepositoryUrl] = useState("");

  async function loadProjects() {
    try {
      setLoading(true);
      setError("");

      const data = await getProjects();
      setProjects(data as Project[]);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load projects",
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadGitHubRepositories() {
    try {
      setLoadingRepositories(true);
      setError("");

      const data = await getGitHubRepositories();
      setRepositories(data);

      if (data.length > 0) {
        setRepositoryUrl(data[0].html_url);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load GitHub repositories",
      );
    } finally {
      setLoadingRepositories(false);
    }
  }

  function openCreateModal() {
    setName("");
    setRepositoryUrl("");
    setShowCreate(true);
    loadGitHubRepositories();
  }

  async function handleCreateProject(event: React.FormEvent) {
    event.preventDefault();

    if (!name.trim() || !repositoryUrl) {
      return;
    }

    try {
      setCreating(true);
      setError("");

      await createProject(name.trim(), repositoryUrl);

      setShowCreate(false);
      setName("");
      setRepositoryUrl("");

      await loadProjects();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create project",
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteProject(projectId: number) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this project?",
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");

      await deleteProject(projectId);
      await loadProjects();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete project",
      );
    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-white">
            Projects
          </h1>

          <p className="mt-2 text-sm text-zinc-400">
            Manage the repositories Syntra can work on.
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-medium text-black transition hover:bg-zinc-200"
        >
          <Plus size={17} />
          Add Project
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {loading ? (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-8 text-center text-sm text-zinc-400">
          Loading projects...
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/40 px-6 py-16 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-zinc-800">
            <FolderGit2 size={25} className="text-zinc-400" />
          </div>

          <h2 className="mt-5 text-lg font-medium text-white">
            No projects yet
          </h2>

          <p className="mx-auto mt-2 max-w-md text-sm text-zinc-500">
            Connect one of your GitHub repositories and let Syntra
            analyze, modify, test, and create pull requests for your
            codebase.
          </p>

          <button
            onClick={openCreateModal}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-medium text-black transition hover:bg-zinc-200"
          >
            <Plus size={17} />
            Add Project
          </button>
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              to={`/projects/${project.id}`}
              className="group block rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 transition hover:border-zinc-700 hover:bg-zinc-900"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-zinc-800">
                    <FolderGit2
                      size={20}
                      className="text-zinc-300"
                    />
                  </div>

                  <div className="min-w-0">
                    <h2 className="truncate font-medium text-white">
                      {project.name}
                    </h2>

                    <p className="mt-1 truncate text-xs text-zinc-500">
                      {project.repository_url
                        .replace("https://github.com/", "")
                        .replace(".git", "")}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    handleDeleteProject(project.id);
                  }}
                  className="rounded-lg p-2 text-zinc-500 opacity-0 transition hover:bg-red-500/10 hover:text-red-400 group-hover:opacity-100"
                  title="Delete project"
                >
                  <Trash2 size={17} />
                </button>
              </div>

              <div className="mt-5 flex items-center justify-between">
                <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400">
                  Connected
                </span>

                <span
                  onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    window.open(
                      project.repository_url,
                      "_blank",
                      "noopener,noreferrer",
                    );
                  }}
                  className="flex items-center gap-1.5 text-xs text-zinc-400 transition hover:text-white"
                >
                  GitHub
                  <ExternalLink size={14} />
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white">
                  Add Project
                </h2>

                <p className="mt-1 text-sm text-zinc-500">
                  Select a repository connected to your GitHub account.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="rounded-lg p-2 text-zinc-500 transition hover:bg-zinc-800 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            <form
              onSubmit={handleCreateProject}
              className="mt-6 space-y-5"
            >
              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  Project Name
                </label>

                <input
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="My AI Project"
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-white outline-none transition placeholder:text-zinc-600 focus:border-zinc-600"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  GitHub Repository
                </label>

                {loadingRepositories ? (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-zinc-500">
                    Loading your repositories...
                  </div>
                ) : repositories.length === 0 ? (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-zinc-500">
                    No GitHub repositories found.
                  </div>
                ) : (
                  <select
                    value={repositoryUrl}
                    onChange={(event) =>
                      setRepositoryUrl(event.target.value)
                    }
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-white outline-none transition focus:border-zinc-600"
                    required
                  >
                    {repositories.map((repository) => (
                      <option
                        key={repository.id}
                        value={repository.html_url}
                      >
                        {repository.full_name}
                        {repository.private ? " • Private" : ""}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {repositoryUrl && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 px-4 py-3">
                  <p className="text-xs text-zinc-500">
                    Selected repository
                  </p>

                  <p className="mt-1 truncate text-sm text-zinc-300">
                    {repositoryUrl}
                  </p>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="rounded-xl border border-zinc-800 px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-zinc-900"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={
                    creating ||
                    loadingRepositories ||
                    !name.trim() ||
                    !repositoryUrl
                  }
                  className="rounded-xl bg-white px-4 py-2.5 text-sm font-medium text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Create Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
