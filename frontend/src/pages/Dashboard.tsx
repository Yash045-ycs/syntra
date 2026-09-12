import {
Bot,
ChevronRight,
CircleCheck,
FolderGit2,
GitPullRequest,
Plus,
Sparkles,
} from "lucide-react";

const projects = [
{
name: "LifeLedger",
repo: "Yash045-ycs/LifeLedgers",
status: "Ready",
language: "TypeScript",
updated: "2 hours ago",
},
{
name: "Syntra",
repo: "Yash045-ycs/syntra",
status: "Active",
language: "Python",
updated: "Today",
},
{
name: "RAG Test Repo",
repo: "Yash045-ycs/rag_test_repo",
status: "PR Open",
language: "Python",
updated: "Today",
},
];

const activities = [
{
icon: CircleCheck,
title: "Validation completed",
description: "All checks passed for RAG Test Repo",
time: "12 min ago",
},
{
icon: GitPullRequest,
title: "Pull request created",
description: "Syntra opened PR #2",
time: "18 min ago",
},
{
icon: Bot,
title: "Agent run completed",
description: "Shipping cost parameter added",
time: "20 min ago",
},
];

function Dashboard() {
return ( <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8"> <section className="mb-8"> <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"> <div> <div className="mb-2 flex items-center gap-2 text-xs font-medium text-zinc-500"> <Sparkles size={13} />
AUTONOMOUS ENGINEERING </div>

        <h1 className="text-3xl font-semibold tracking-tight text-white">
          Good evening, Yash.
        </h1>

        <p className="mt-2 max-w-xl text-sm leading-6 text-zinc-500">
          Build, modify and validate software with an AI agent that
          understands your codebase.
        </p>
      </div>

      <button className="flex items-center justify-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-medium text-black transition hover:bg-zinc-200">
        <Plus size={16} />
        New Project
      </button>
    </div>
  </section>

  <section className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
    <StatCard
      label="Projects"
      value="3"
      detail="Connected repositories"
      icon={FolderGit2}
    />

    <StatCard
      label="Agent Runs"
      value="12"
      detail="8 completed successfully"
      icon={Bot}
    />

    <StatCard
      label="Pull Requests"
      value="4"
      detail="2 awaiting review"
      icon={GitPullRequest}
    />

    <StatCard
      label="Success Rate"
      value="92%"
      detail="Last 30 agent runs"
      icon={CircleCheck}
    />
  </section>

  <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
    <section className="rounded-2xl border border-white/[0.07] bg-[#0d0d10]">
      <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-white">
            Projects
          </h2>

          <p className="mt-1 text-xs text-zinc-600">
            Repositories connected to Syntra
          </p>
        </div>

        <button className="text-xs text-zinc-500 hover:text-white">
          View all
        </button>
      </div>

      <div className="divide-y divide-white/[0.05]">
        {projects.map((project) => (
          <ProjectRow key={project.name} project={project} />
        ))}
      </div>
    </section>

    <section className="rounded-2xl border border-white/[0.07] bg-[#0d0d10]">
      <div className="border-b border-white/[0.06] px-5 py-4">
        <h2 className="text-sm font-semibold text-white">
          Recent activity
        </h2>

        <p className="mt-1 text-xs text-zinc-600">
          Latest agent events
        </p>
      </div>

      <div className="divide-y divide-white/[0.05]">
        {activities.map((activity) => {
          const Icon = activity.icon;

          return (
            <div
              key={activity.title}
              className="flex gap-3 px-5 py-4"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/[0.06] bg-white/[0.025]">
                <Icon size={14} className="text-zinc-400" />
              </div>

              <div className="min-w-0">
                <div className="text-xs font-medium text-zinc-200">
                  {activity.title}
                </div>

                <div className="mt-1 text-xs leading-5 text-zinc-600">
                  {activity.description}
                </div>

                <div className="mt-1.5 text-[10px] text-zinc-700">
                  {activity.time}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  </div>

  <section className="mt-6 overflow-hidden rounded-2xl border border-white/[0.07] bg-[#0d0d10]">
    <div className="flex flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/[0.07] bg-white/[0.025]">
          <Bot size={18} className="text-zinc-300" />
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-white">
              Start an agent run
            </h2>

            <span className="rounded-full border border-emerald-500/20 bg-emerald-500/5 px-2 py-0.5 text-[10px] text-emerald-400">
              Ready
            </span>
          </div>

          <p className="mt-1 text-xs leading-5 text-zinc-600">
            Describe a change in natural language and let Syntra analyze,
            modify and validate your repository.
          </p>
        </div>
      </div>

      <button className="flex items-center justify-center gap-2 whitespace-nowrap rounded-lg border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-xs font-medium text-zinc-200 hover:bg-white/[0.06]">
        Open Agent
        <ChevronRight size={14} />
      </button>
    </div>
  </section>
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
return ( <div className="rounded-2xl border border-white/[0.07] bg-[#0d0d10] p-5"> <div className="mb-5 flex items-center justify-between"> <span className="text-xs text-zinc-500">{label}</span> <Icon size={16} className="text-zinc-600" /> </div>

  <div className="text-2xl font-semibold tracking-tight text-white">
    {value}
  </div>

  <div className="mt-1 text-[11px] text-zinc-600">{detail}</div>
</div>

);
}

function ProjectRow({
project,
}: {
project: {
name: string;
repo: string;
status: string;
language: string;
updated: string;
};
}) {
return ( <button className="flex w-full items-center gap-4 px-5 py-4 text-left transition hover:bg-white/[0.025]"> <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/[0.06] bg-white/[0.025]"> <FolderGit2 size={16} className="text-zinc-400" /> </div>

  <div className="min-w-0 flex-1">
    <div className="text-xs font-medium text-zinc-200">
      {project.name}
    </div>

    <div className="mt-1 truncate text-[11px] text-zinc-600">
      {project.repo}
    </div>
  </div>

  <div className="hidden text-right sm:block">
    <div className="text-[11px] text-zinc-500">
      {project.language}
    </div>

    <div className="mt-1 text-[10px] text-zinc-700">
      {project.updated}
    </div>
  </div>

  <span className="hidden rounded-full border border-white/[0.08] px-2 py-1 text-[10px] text-zinc-400 sm:block">
    {project.status}
  </span>

  <ChevronRight size={14} className="text-zinc-700" />
</button>
);
}

export default Dashboard;
