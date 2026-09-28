# Consumer Identity Verification — Phase 2 实现报告

**状态**：`PHASE 2 COMPLETE / WAITING OWNER PHASE 3 AUTHORIZATION`
**日期**：2026-09-16
**依据**：PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md §4.2

---

## 1. 交付物

| 文件 | 类型 | 说明 |
|---|---|---|
| `backend/app/core/manifest_identity.py` | 实现 | M1 Manifest Reader |
| `backend/tests/test_manifest_identity.py` | 测试 | 17 单元测试，17/17 PASS |

## 2. 接口签名

```python
@dataclass(frozen=True)
class ManifestIdentity:
    source_content_sha256: str | None   # 64-char lowercase hex, or None

class ManifestReadError(Exception): ...

def read_manifest_identity(manifest_path: Path) -> ManifestIdentity: ...
```

## 3. 设计约束符合性

| 约束 | 验证 |
|---|---|
| 不读 source bytes ✅ | 仅 `read_text()` manifest JSON |
| 不计算 sha256 ✅ | 零 hashlib import |
| 不访问 IR ✅ | 零 IR 相关代码 |
| 不做 mismatch 判断 ✅ | 仅提取，不比对 |
| 不接入 runner ✅ | 独立模块 |
| 不修改 hashing.py ✅ | 未 touch |
| 不修改 schema ✅ | 未 touch |
| 不修改 Gate/Admission ✅ | 未 touch |
| path 不参与 identity ✅ | `ManifestIdentity` 仅含 `source_content_sha256` 字段 |

## 4. 行为规范（冻结）

| 输入 | 输出 |
|---|---|
| `source_content_sha256` = 64 位小写 hex | `ManifestIdentity(source_content_sha256=sha)` |
| `source_content_sha256` 不存在 | `ManifestIdentity(source_content_sha256=None)` |
| `source_content_sha256` = `""` | `ManifestIdentity(source_content_sha256=None)` |
| `source_content_sha256` = `null` | `ManifestIdentity(source_content_sha256=None)` |
| `source_content_sha256` = 非 hex / 非 64 位 / 大写 / 非 str | `ManifestReadError` |
| 文件不存在 | `ManifestReadError` |
| JSON 解析失败 | `ManifestReadError` |
| JSON 非 object（如 array） | `ManifestReadError` |

## 5. 测试结果

```
17 passed in 0.07s
```

| 测试组 | 数量 | 覆盖内容 |
|---|---|---|
| TestNormalRead | 3 | 正常读取、frozen dataclass、hex 格式 |
| TestMissingHash | 3 | 缺失 / 空字符串 / null → None |
| TestMalformedManifest | 7 | 文件不存在 / JSON 错误 / 非法 hex（大写/短/非hex/非str） |
| TestExtraFields | 2 | 额外字段不影响读取、嵌套 units 不影响 |
| TestPathNotIdentity | 2 | dataclass 无 path 字段、source_file 不影响 identity |

## 6. git diff 说明

| 操作 | 文件 |
|---|---|
| 新增 | `backend/app/core/manifest_identity.py` |
| 新增 | `backend/tests/test_manifest_identity.py` |

零修改现有文件。

## 7. 边界

- 未实现 M3 IR Reader / M4 Identity Verifier / M5 Identity Gate
- 未修改 Contract f4941ff / Producer 数据 / Source bytes / Schema / Gate
- 未修改 `hashing.py` / `raw_bytes_identity.py` / `manifest_reader.py`
