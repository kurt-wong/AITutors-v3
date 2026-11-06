/** Admin 布局：GlobalNav + 内容区（max-w 1440px）。
 *  VIS-INSPECT-V1：卷库切换后以 key 重挂载内容区强制重取，并清理残留路由
 *  （切换前的题号 / document_id 只属于旧卷库，保留会 404 或空列表）。 */

import { useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { GlobalNav } from "./GlobalNav";

export function AdminLayout() {
  const [volumeKey, setVolumeKey] = useState(0);
  const navigate = useNavigate();

  function handleVolumeChanged() {
    setVolumeKey((k) => k + 1);
    // 切换卷库即换数据域：回到干净的题目列表，避免旧题号/旧筛选残留
    navigate("/admin/questions");
  }

  return (
    <>
      <GlobalNav onVolumeChanged={handleVolumeChanged} />
      <main className="mx-auto w-full max-w-[1440px] flex-1 px-6 py-6">
        <div key={volumeKey}>
          <Outlet />
        </div>
      </main>
    </>
  );
}
