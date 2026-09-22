import {
  Activity as ActivityIcon,
  FolderGit2,
  GitBranch,
  GitPullRequest,
  LayoutDashboard,
  LogIn,
  LogOut,
  Menu,
  Settings,
  Sparkles,
  Terminal,
  User,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import Register from "./pages/Register";
import Login from "./pages/Login";
import ProtectedRoute from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import Projects from "./pages/Projects";
import AgentRuns from "./pages/AgentRuns";
import PullRequests from "./pages/PullRequests";
import GitHub from "./pages/GitHub";
import ActivityLogs from "./pages/ActivityLogs";
import SettingsPage from "./pages/Settings";
import AgentRunDetails from "./pages/AgentRunDetails";
import ProjectDetails from "./pages/ProjectDetails";
import Activity from "./pages/Activity";

const navigation = [
  {
    label: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Projects",
    path: "/projects",
    icon: FolderGit2,
  },
  {
    label: "Agent Runs",
    path: "/runs",
    icon: ActivityIcon,
  },
  {
    label: "Pull Requests",
    path: "/pull-requests",
    icon: GitPullRequest,
  },
  {
    label: "Activity",
    path: "/activity",
    icon: ActivityIcon,
  },
];

const developerNavigation = [
  {
    label: "GitHub",
    path: "/github",
    icon: GitBranch,
  },
  {
    label: "Activity Logs",
    path: "/logs",
    icon: Terminal,
  },
  {
    label: "Settings",
    path: "/settings",
    icon: Settings,
  },
];

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [loggedIn, setLoggedIn] = useState(
    Boolean(localStorage.getItem("syntra_token")),
  );

  const location = useLocation();
  const navigate = useNavigate();

  const currentNavigation = [
    ...navigation,
    ...developerNavigation,
  ].find((item) => item.path === location.pathname);

  useEffect(() => {
    setLoggedIn(Boolean(localStorage.getItem("syntra_token")));
    setAccountOpen(false);
  }, [location.pathname]);

  function handleLogout() {
    localStorage.removeItem("syntra_token");
    setLoggedIn(false);
    setAccountOpen(false);
    navigate("/login");
  }

  function handleAccountClick() {
    if (!loggedIn) {
      navigate("/login");
      return;
    }

    setAccountOpen((current) => !current);
  }

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="flex min-h-screen">
        <aside
          className={`fixed inset-y-0 left-0 z-50 w-64 border-r border-white/[0.06] bg-[#0c0c0f] transition-transform duration-200 lg:static lg:translate-x-0 ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex h-full flex-col">
            <div className="flex h-16 items-center justify-between border-b border-white/[0.06] px-5">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-black">
                  <Sparkles size={17} strokeWidth={2.5} />
                </div>

                <div>
                  <div className="text-[15px] font-semibold tracking-tight">
                    Syntra
                  </div>

                  <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">
                    AI Engineer
                  </div>
                </div>
              </div>

              <button
                onClick={() => setSidebarOpen(false)}
                className="rounded-md p-1.5 text-zinc-500 hover:bg-white/[0.05] hover:text-zinc-200 lg:hidden"
              >
                <X size={18} />
              </button>
            </div>

            <div className="flex-1 px-3 py-5">
              <div className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-600">
                Workspace
              </div>

              <nav className="space-y-1">
                {navigation.map((item) => (
                  <SidebarLink
                    key={item.path}
                    {...item}
                    onClick={() => setSidebarOpen(false)}
                  />
                ))}
              </nav>

              <div className="mb-2 mt-8 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-600">
                Developer
              </div>

              <nav className="space-y-1">
                {developerNavigation.map((item) => (
                  <SidebarLink
                    key={item.path}
                    {...item}
                    onClick={() => setSidebarOpen(false)}
                  />
                ))}
              </nav>
            </div>

            <div className="border-t border-white/[0.06] p-4">
              <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs text-zinc-400">
                    Agent status
                  </span>

                  <span className="flex items-center gap-1.5 text-[11px] text-emerald-400">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                    Online
                  </span>
                </div>

                <div className="text-xs text-zinc-600">
                  Gemini · RAG · GitHub
                </div>
              </div>
            </div>
          </div>
        </aside>

        {sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          />
        )}

        <main className="min-w-0 flex-1">
          <header className="flex h-16 items-center justify-between border-b border-white/[0.06] px-5 sm:px-8">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-zinc-400 hover:bg-white/[0.05] hover:text-white lg:hidden"
            >
              <Menu size={20} />
            </button>

            <div className="hidden text-sm text-zinc-500 lg:block">
              Workspace /{" "}
              <span className="text-zinc-300">
                {currentNavigation?.label || "Dashboard"}
              </span>
            </div>

            <div className="relative ml-auto">
              {loggedIn ? (
                <>
                  <button
                    type="button"
                    onClick={handleAccountClick}
                    className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-zinc-800 text-xs font-semibold text-white transition hover:border-white/20 hover:bg-zinc-700"
                    aria-label="Open account menu"
                  >
                    Y
                  </button>

                  {accountOpen && (
                    <>
                      <button
                        type="button"
                        onClick={() => setAccountOpen(false)}
                        className="fixed inset-0 z-40 cursor-default"
                        aria-label="Close account menu"
                      />

                      <div className="absolute right-0 top-11 z-50 w-56 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 shadow-2xl">
                        <div className="border-b border-zinc-800 px-4 py-3">
                          <p className="text-xs font-medium text-white">
                            Syntra Account
                          </p>

                          <p className="mt-1 text-[11px] text-zinc-600">
                            Manage your account
                          </p>
                        </div>

                        <div className="p-1.5">
                          <button
                            type="button"
                            onClick={() => {
                              setAccountOpen(false);
                              navigate("/settings");
                            }}
                            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-xs text-zinc-400 transition hover:bg-white/[0.05] hover:text-white"
                          >
                            <User size={15} />
                            Account & Settings
                          </button>

                          <button
                            type="button"
                            onClick={handleLogout}
                            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-xs text-red-400 transition hover:bg-red-500/10"
                          >
                            <LogOut size={15} />
                            Log out
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </>
              ) : (
                <button
                  type="button"
                  onClick={() => navigate("/login")}
                  className="flex items-center gap-2 rounded-lg bg-white px-3.5 py-2 text-xs font-medium text-black transition hover:bg-zinc-200"
                >
                  <LogIn size={14} />
                  Log in
                </button>
              )}
            </div>
          </header>

          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route path="/settings" element={<SettingsPage />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/projects" element={<Projects />} />
              <Route
  path="/projects/:projectId"
  element={<ProjectDetails />}
/>
              <Route path="/runs" element={<AgentRuns />} />
              <Route
    path="/projects/:projectId/runs/:runId"
    element={<AgentRunDetails />}
  />
              <Route path="/pull-requests" element={<PullRequests />} />
              <Route path="/github" element={<GitHub />} />
              <Route path="/logs" element={<ActivityLogs />} />
              <Route path="/activity" element={<Activity />} />
            </Route>
          </Routes>
        </main>
      </div>
    </div>
  );
}

function SidebarLink({
  label,
  path,
  icon: Icon,
  onClick,
}: {
  label: string;
  path: string;
  icon: React.ElementType;
  onClick: () => void;
}) {
  return (
    <NavLink
      to={path}
      onClick={onClick}
      end={path === "/"}
      className={({ isActive }) =>
        `flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-xs transition ${
          isActive
            ? "bg-white/[0.07] text-white"
            : "text-zinc-500 hover:bg-white/[0.04] hover:text-zinc-200"
        }`
      }
    >
      <Icon size={16} strokeWidth={1.8} />
      <span>{label}</span>
    </NavLink>
  );
}

export default App;
