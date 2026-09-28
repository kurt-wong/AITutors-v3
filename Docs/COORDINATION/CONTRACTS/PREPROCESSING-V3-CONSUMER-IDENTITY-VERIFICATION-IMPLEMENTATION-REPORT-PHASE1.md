# Consumer Identity Verification — Phase 1 Implementation Report

## Status: IMPLEMENTED / TESTS PASS / PHASE 1 ONLY

**Date**: 2026-09-16
**Phase**: 1 — Raw Bytes Identity Layer (M2)
**Scope**: Consumer Identity Verification only
**Author**: Owner-authorized implementation

---

## 1. What Was Implemented

### Module: `backend/app/core/raw_bytes_identity.py`

**Version**: 1.0.0

**Exports**:
- `RawBytesIdentity` — frozen dataclass `{bytes_source: str, sha256: str}`
- `load_raw_bytes_identity(source_path: Path) -> RawBytesIdentity`
- `RAW_BYTES_IDENTITY_VERSION = "1.0.0"`

**Design compliance**:
| Requirement | Implementation | Status |
|---|---|---|
| `read_bytes()` | `source_path.read_bytes()` | ✅ |
| `hashlib.sha256(raw_bytes).hexdigest()` | Direct, no wrapper | ✅ |
| Forbidden: `read_text()` | Not used anywhere | ✅ |
| Forbidden: `sha256_hex()` | Not imported | ✅ |
| Forbidden: `canonical_json` | Not imported | ✅ |
| Forbidden: text normalization | None applied | ✅ |
| Output: `{bytes_source, sha256}` | Frozen dataclass | ✅ |

---

## 2. Tests

### Module: `backend/tests/test_raw_bytes_identity.py`

**Result**: 10/10 PASS

| Test | Coverage | Status |
|---|---|---|
| `test_crlf_and_lf_produce_different_sha` | CRLF 保真: CRLF ≠ LF bytes | ✅ |
| `test_crlf_exact_hash_matches_raw_bytes` | CRLF 精确 hash 等于 raw bytes sha256 | ✅ |
| `test_trailing_newline_changes_hash` | Trailing newline 保真 | ✅ |
| `test_unicode_bytes_hashed_as_raw_bytes` | Unicode (中文/emoji) 按 bytes 计算 | ✅ |
| `test_bom_preserved` | BOM bytes 保留在 hash 输入 | ✅ |
| `test_text_hash_differs_from_bytes_hash` | text 路径 hash ≠ bytes 路径 hash (FACT-031) | ✅ |
| `test_returns_frozen_dataclass` | 返回类型/字段正确 | ✅ |
| `test_sha256_is_lowercase_64_hex` | 输出格式 64-char lowercase hex | ✅ |
| `test_missing_file_raises` | FileNotFoundError 错误路径 | ✅ |
| `test_does_not_use_text_path_for_hashing` | 防回归: 精确验证无 read_text 参与 | ✅ |

**TDD flow**: RED (ModuleNotFoundError) → GREEN (10/10 pass) → verified no existing tests broken.

---

## 3. What Was NOT Implemented (Phase 1 boundary)

Per Owner instruction "只提交 Phase 1。不要实现 Manifest / IR / Gate":

- ❌ M1 Manifest Reader — not implemented
- ❌ M3 IR Reader — not implemented
- ❌ M4 Identity Verifier — not implemented
- ❌ M5 Consumer Identity Gate — not implemented

---

## 4. Forbidden Surface Verification

No modifications to:
- Freeze Artifact f4941ff — untouched
- Producer manifest / source bytes / IR data — untouched
- Schema — no migrations
- Gate/Admission business logic — untouched
- `app/core/hashing.py` — untouched (sha256_hex not reused)

---

## 5. Key Design Decisions

1. **Module location**: `app/core/raw_bytes_identity.py` — alongside `hashing.py` as a cross-cutting identity primitive, not a domain module.

2. **`RawBytesIdentity` as frozen dataclass**: Immutable value object. `bytes_source` is locator (string path), `sha256` is identity key.

3. **No dependency on `app.core.hashing`**: Deliberately independent module. The V3 hash family (`sha256_hex` via `canonical_json`) must not leak into raw bytes identity computation.

4. **conftest `migrated_db` override**: Test module overrides the session-scoped autouse fixture since these are pure unit tests with no DB dependency.

---

## 6. Files Changed

| File | Action |
|---|---|
| `backend/app/core/raw_bytes_identity.py` | NEW — M2 implementation |
| `backend/tests/test_raw_bytes_identity.py` | NEW — 10 unit tests |

---

## Status

**PHASE 1 COMPLETE. WAITING OWNER PHASE 2 AUTHORIZATION.**
