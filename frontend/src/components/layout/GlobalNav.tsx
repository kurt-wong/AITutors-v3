/** 全局导航：黑色 44px 条（UI.md §3.1）。 */

import { NavLink } from "react-router-dom";

const links = [
  { to: "/admin", label: "Workspace" },
  { to: "/admin/documents", label: "Documents" },
  { to: "/admin/documents/upload", label: "Import" },
];

export function GlobalNav() {
  return (
    <nav className="flex h-11 items-center gap-6 bg-surface-tile px-6 text-[13px] text-white">
      <span className="font-display font-semibold tracking-tight">
        AITutor V3
      </span>
      <span className="text-body-muted">Review Console</span>
      <div className="ml-auto flex gap-4">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/admin"}
            className={({ isActive }) =>
              isActive
                ? "text-primary-on-dark"
                : "text-body-muted hover:text-white transition-colors"
            }
          >
            {l.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
