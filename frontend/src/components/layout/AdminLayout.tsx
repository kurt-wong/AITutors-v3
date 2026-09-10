/** Admin 布局：GlobalNav + 内容区（max-w 1440px）。 */

import { Outlet } from "react-router-dom";
import { GlobalNav } from "./GlobalNav";

export function AdminLayout() {
  return (
    <>
      <GlobalNav />
      <main className="mx-auto w-full max-w-[1440px] flex-1 px-6 py-6">
        <Outlet />
      </main>
    </>
  );
}
