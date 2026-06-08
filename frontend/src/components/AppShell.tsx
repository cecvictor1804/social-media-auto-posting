import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Calendar, LayoutList, LogOut, Megaphone, Menu, Moon, PenSquare, Plug, Sun, X } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/theme-provider";

const NAV = [
  { to: "/", label: "Compose", Icon: PenSquare, end: true },
  { to: "/queue", label: "Queue", Icon: LayoutList, end: false },
  { to: "/calendar", label: "Calendar", Icon: Calendar, end: false },
  { to: "/accounts", label: "Accounts", Icon: Plug, end: false },
];

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme" title="Toggle theme">
      {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </Button>
  );
}

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <>
      {NAV.map(({ to, label, Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
              isActive
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )
          }
        >
          <Icon className="h-[18px] w-[18px]" />
          {label}
        </NavLink>
      ))}
    </>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-2.5">
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-sky-500 text-white shadow-sm">
        <Megaphone className="h-5 w-5" />
      </span>
      <div className="leading-tight">
        <div className="text-sm font-bold">Auto-Poster</div>
        <div className="text-[11px] text-muted-foreground">Schedule everywhere</div>
      </div>
    </div>
  );
}

export function AppShell() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [mobileOpen, setMobileOpen] = useState(false);

  async function logout() {
    await api.post("/api/auth/logout").catch(() => {});
    qc.clear();
    navigate("/login");
  }

  return (
    <div className="app-bg min-h-screen lg:flex">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r bg-card/60 backdrop-blur lg:flex">
        <div className="px-5 py-5">
          <Brand />
        </div>
        <nav className="flex flex-1 flex-col gap-1 px-3">
          <NavItems />
        </nav>
        <div className="flex items-center justify-between border-t px-3 py-3">
          <Button variant="ghost" size="sm" className="text-muted-foreground" onClick={logout}>
            <LogOut className="h-4 w-4" /> Logout
          </Button>
          <ThemeToggle />
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="flex items-center justify-between border-b bg-card/80 px-4 py-3 backdrop-blur lg:hidden">
        <Brand />
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <Button variant="ghost" size="icon" onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </Button>
        </div>
      </header>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="absolute left-0 top-0 h-full w-72 border-r bg-card p-4">
            <div className="mb-4 flex items-center justify-between">
              <Brand />
              <Button variant="ghost" size="icon" onClick={() => setMobileOpen(false)} aria-label="Close menu">
                <X className="h-5 w-5" />
              </Button>
            </div>
            <nav className="flex flex-col gap-1">
              <NavItems onNavigate={() => setMobileOpen(false)} />
            </nav>
            <Button variant="ghost" size="sm" className="mt-4 text-muted-foreground" onClick={logout}>
              <LogOut className="h-4 w-4" /> Logout
            </Button>
          </div>
        </div>
      )}

      <main className="flex-1">
        <div className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-8 sm:py-10">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
