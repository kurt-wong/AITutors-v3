"""Repository 基础设施：事务 session 注入 + 写保护异常（段 A）。不做业务规则。"""

from sqlalchemy.ext.asyncio import AsyncSession


class RepositoryError(RuntimeError):
    """Repository 层显式错误基类（防静默失败）。"""


class SealedVersionError(RepositoryError):
    """document_source_versions.status=sealed 后禁止 UPDATE（10 §4.2 / 40 §6）。"""


class AppendOnlyViolation(RepositoryError):
    """审计/快照/源行 append-only，禁止 UPDATE（10 §3）。"""


class BaseRepository:
    """段 A 写路径统一经 Repository；Domain/Service 不直连 DB。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, obj: object) -> None:
        self._session.add(obj)

    async def flush(self) -> None:
        await self._session.flush()
