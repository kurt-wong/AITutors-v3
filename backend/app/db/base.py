"""SQLAlchemy DeclarativeBase。依赖方向：Base ← models ← __init__ ← env.py（禁反向导入，防 cycle）。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
