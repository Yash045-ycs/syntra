import { useEffect, useState } from "react";
import {
  ExternalLink,
  FolderGit2,
  Plus,
  Trash2,
  X,
} from "lucide-react";

import {
  createProject,
  deleteProject,
  getProjects,
} from "../services/api";

type Project = {
  id: number;
  name: string;
  repository_url: string;
  owner_id: number;
};

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);

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
        err instanceof Error
          ? err.message
          : "Failed to load projects",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  async function handleCreateProject(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!name.trim() || !repositoryUrl.trim()) {
      return;
    }

    try {
      setCreating(true);
      setError("");

      const project = await createProject(
        name.trim(),
        repositoryUrl.trim(),
      );

      setProjects((current): Project[] => [...current, project as Project]);
      setName("");
      setRepositoryUrl("");
      setShowCreate(false);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create project",
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

      setProjects((current) =>
        current.filter((project) => project.id !== projectId),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete project",
      );
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white">
            Projects
          </h1>
          <p className="mt-2 text-sm text-zinc-400">
            Manage the repositories connected to Syntra.
          </p>
        </div>

        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-medium text-zinc-950 transition hover:bg-zinc-200"
        >
          <Plus size={17} />
          Add Project
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3].map((item) => (
            <div
              key={item}
              className="h-48 animate-pulse rounded-2xl border border-zinc-800 bg-zinc-900/60"
            />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="flex min-h-80 flex-col items-center justify-center rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/30 px-6 text-center">
          <div className="mb-4 rounded-xl border border-zinc-800 bg-zinc-900 p-3">
            <FolderGit2 size={25} className="text-zinc-400" />
          </div>

          <h2 className="text-lg font-medium text-white">
            No projects yet
          </h2>

          <p className="mt-2 max-w-md text-sm text-zinc-500">
            Connect a GitHub repository to start using Syntra.
          </p>

          <button
            onClick={() => setShowCreate(true)}
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-zinc-200"
          >
            <Plus size={16} />
            Add your first project
          </button>
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((project) => (
            <div
              key={project.id}
              className="group rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 transition hover:border-zinc-700 hover:bg-zinc-900"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-950">
                  <FolderGit2 size={21} className="text-zinc-300" />
                </div>

                <button
                  onClick={() => handleDeleteProject(project.id)}
                  className="rounded-lg p-2 text-zinc-600 transition hover:bg-red-500/10 hover:text-red-400"
                  title="Delete project"
                >
                  <Trash2 size={17} />
                </button>
              </div>

              <h2 className="mt-5 truncate text-lg font-semibold text-white">
                {project.name}
              </h2>

              <p className="mt-2 truncate text-sm text-zinc-500">
                {project.repository_url
                  .replace("https://github.com/", "")
                  .replace(/\.git$/, "")}
              </p>

              <div className="mt-6 flex items-center justify-between border-t border-zinc-800 pt-4">
                <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400">
                  Connected
                </span>

                <a
                  href={project.repository_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-zinc-400 transition hover:text-white"
                >
                  Repository
                  <ExternalLink size={13} />
                </a>
              </div>
            </div>
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
                  Connect a GitHub repository to Syntra.
                </p>
              </div>

              <button
                onClick={() => setShowCreate(false)}
                className="rounded-lg p-2 text-zinc-500 hover:bg-zinc-900 hover:text-white"
              >
                <X size={19} />
              </button>
            </div>

            <form
              onSubmit={handleCreateProject}
              className="mt-6 space-y-5"
            >
              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  Project name
                </label>

                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="My AI Project"
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3.5 py-3 text-sm text-white outline-none placeholder:text-zinc-600 focus:border-zinc-600"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  GitHub repository URL
                </label>

                <input
                  value={repositoryUrl}
                  onChange={(event) =>
                    setRepositoryUrl(event.target.value)
                  }
                  placeholder="https://github.com/username/repository"
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3.5 py-3 text-sm text-white outline-none placeholder:text-zinc-600 focus:border-zinc-600"
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="rounded-lg border border-zinc-800 px-4 py-2.5 text-sm text-zinc-400 hover:bg-zinc-900 hover:text-white"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-lg bg-white px-5 py-2.5 text-sm font-medium text-zinc-950 transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {creating ? "Connecting..." : "Connect Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}