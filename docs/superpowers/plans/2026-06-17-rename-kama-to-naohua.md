# Rename kama → naohua Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename all "kama" references across the entire project to "naohua", including Python package name, CLI commands, env vars, config paths, class names, and documentation.

**Architecture:** Mechanical find-and-replace across ~106 source/test files, plus directory rename of `src/kama_claude/` → `src/naohua_claude/`. The rename is purely cosmetic — no logic changes.

**Tech Stack:** Python, pyproject.toml, bash (for directory rename and bulk sed)

---

## Rename Mapping

| Old | New | Context |
|-----|-----|---------|
| `kama_claude` | `naohua_claude` | Python package, imports |
| `KamaClaude` | `NaohuaClaude` | Display name, project name |
| `KamaConfig` | `NaohuaConfig` | Config class |
| `KamaTuiApp` | `NaohuaTuiApp` | TUI app class |
| `KAMA_` | `NAOHUA_` | Env var prefix (KAMA_HOST, KAMA_PORT, etc.) |
| `~/.kama/` | `~/.naohua/` | Config/data/log paths |
| `.kama/` | `.naohua/` | Project-local config dir |
| `kama-core` | `naohua-core` | CLI entry point |
| `kama-tui` | `naohua-tui` | CLI entry point |
| `kama` (CLI) | `naohua` | CLI entry point |
| `kamacoder` | `naohuacoder` | Domain references in README |
| `kama logs` | `naohua logs` | Log path reference |
| `卡码` | `脑花` | Chinese brand name in README |
| `卡哥` | `脑花哥` | Chinese nickname in README |

## Files Affected

- **65 source files** in `src/kama_claude/`
- **41 test files** in `tests/`
- **1 script**: `scripts/gen_protocol_doc.py`
- **1 skill**: `src/kama_claude/core/skills/builtin/init.md`
- **1 trace script**: `trace_permission_flow.py`
- **1 generated doc**: `WIRE_PROTOCOL.md` (regenerated from models)
- **6 config/doc files**: `pyproject.toml`, `.env`, `.env.example`, `CLAUDE.md`, `AGENT.md`, `RUNBOOK.md`, `README.md`

---

### Task 1: Rename source directory

**Files:**
- Rename: `src/kama_claude/` → `src/naohua_claude/`

- [ ] **Step 1: Rename the directory**

```bash
mv src/kama_claude src/naohua_claude
```

- [ ] **Step 2: Verify directory exists**

```bash
ls src/naohua_claude/__init__.py
```

Expected: file exists

---

### Task 2: Update pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Apply all replacements in pyproject.toml**

Replace in `pyproject.toml`:
- `name = "KamaClaude"` → `name = "NaohuaClaude"`
- `kama_claude.cli.main:main` → `naohua_claude.cli.main:main`
- `kama_claude.core.app:run` → `naohua_claude.core.app:run`
- `kama_claude.tui.__main__:main` → `naohua_claude.tui.__main__:main`
- `kama = "` → `naohua = "`
- `kama-core = "` → `naohua-core = "`
- `kama-tui = "` → `naohua-tui = "`
- `packages = ["src/kama_claude"]` → `packages = ["src/naohua_claude"]`
- Comment: `# KamaClaude` → `# NaohuaClaude`
- Comment: `kama` → `naohua` (in entry point comments)
- `textual>=0.75` comment: `kama-tui` → `naohua-tui`

---

### Task 3: Bulk rename Python imports and references

**Files:**
- Modify: All 65 `.py` files in `src/naohua_claude/`
- Modify: All 41 `.py` files in `tests/`
- Modify: `scripts/gen_protocol_doc.py`

- [ ] **Step 1: Replace `kama_claude` → `naohua_claude` in all Python files**

Use bash to replace across all `.py` files under `src/`, `tests/`, and `scripts/`:

```bash
find src tests scripts -name '*.py' -exec sed -i 's/kama_claude/naohua_claude/g' {} +
```

- [ ] **Step 2: Replace `KamaClaude` → `NaohuaClaude` in all Python files**

```bash
find src tests scripts -name '*.py' -exec sed -i 's/KamaClaude/NaohuaClaude/g' {} +
```

- [ ] **Step 3: Replace `KamaConfig` → `NaohuaConfig` in all Python files**

```bash
find src tests scripts -name '*.py' -exec sed -i 's/KamaConfig/NaohuaConfig/g' {} +
```

- [ ] **Step 4: Replace `KamaTuiApp` → `NaohuaTuiApp` in all Python files**

```bash
find src tests scripts -name '*.py' -exec sed -i 's/KamaTuiApp/NaohuaTuiApp/g' {} +
```

- [ ] **Step 5: Replace `KAMA_` → `NAOHUA_` env var prefix in all Python files**

```bash
find src tests scripts -name '*.py' -exec sed -i 's/KAMA_/NAOHUA_/g' {} +
```

- [ ] **Step 6: Replace `~/.kama/` → `~/.naohua/` in all Python files**

```bash
find src tests scripts -name '*.py' -exec sed -i 's|~/\.kama/|~/.naohua/|g' {} +
```

- [ ] **Step 7: Replace `.kama/` → `.naohua/` in all Python files**

```bash
find src tests scripts -name '*.py' -exec sed -i 's|\.kama/|.naohua/|g' {} +
```

- [ ] **Step 8: Replace `kama-tui` → `naohua-tui` in all Python files**

```bash
find src tests scripts -name '*.py' -exec sed -i 's/kama-tui/naohua-tui/g' {} +
```

- [ ] **Step 9: Replace `kama-core` → `naohua-core` in all Python files**

```bash
find src tests scripts -name '*.py' -exec sed -i 's/kama-core/naohua-core/g' {} +
```

- [ ] **Step 10: Verify no `kama` references remain in Python files**

```bash
grep -ri 'kama' src/ tests/ scripts/ --include='*.py' || echo "No kama references found - clean!"
```

Expected: "No kama references found - clean!"

---

### Task 4: Update skills markdown

**Files:**
- Modify: `src/naohua_claude/core/skills/builtin/init.md`

- [ ] **Step 1: Replace references in init.md**

Replace:
- `.kama/context.md` → `.naohua/context.md`
- `.kama/` → `.naohua/`

```bash
sed -i 's|\.kama/|.naohua/|g' src/naohua_claude/core/skills/builtin/init.md
```

---

### Task 5: Update .env and .env.example

**Files:**
- Modify: `.env`
- Modify: `.env.example`

- [ ] **Step 1: Replace env var names in .env**

Replace all `KAMA_` → `NAOHUA_` and `~/.kama/` → `~/.naohua/` in `.env`:

```bash
sed -i 's/KAMA_/NAOHUA_/g; s|~/\.kama/|~/.naohua/|g; s/KamaClaude/NaohuaClaude/g' .env
```

- [ ] **Step 2: Replace env var names in .env.example**

```bash
sed -i 's/KAMA_/NAOHUA_/g; s|~/\.kama/|~/.naohua/|g; s/KamaClaude/NaohuaClaude/g' .env.example
```

---

### Task 6: Update documentation files

**Files:**
- Modify: `CLAUDE.md`
- Modify: `AGENT.md`
- Modify: `RUNBOOK.md`
- Modify: `README.md`

- [ ] **Step 1: Update CLAUDE.md**

Replace:
- `kama-core` → `naohua-core`
- `kama-tui` → `naohua-tui`
- `kama` (CLI) → `naohua`
- `kama_claude` → `naohua_claude`
- `KamaClaude` → `NaohuaClaude`
- `KAMA_` → `NAOHUA_`
- `~/.kama/` → `~/.naohua/`

- [ ] **Step 2: Update AGENT.md**

Same replacements as CLAUDE.md.

- [ ] **Step 3: Update RUNBOOK.md**

Same replacements. Also update:
- `kama.toml` → `naohua.toml` (if referenced)
- `pgrep -f kama-core` → `pgrep -f naohua-core`

- [ ] **Step 4: Update README.md**

Replace:
- `KamaClaude` → `NaohuaClaude`
- `kama` CLI → `naohua` CLI
- `kama-core` → `naohua-core`
- `kama-tui` → `naohua-tui`
- `kamacoder` → `naohuacoder` (domain references)
- `卡码` → `脑花` (Chinese brand name)
- `卡哥` → `脑花哥` (Chinese nickname)

---

### Task 7: Update trace script and regenerate WIRE_PROTOCOL.md

**Files:**
- Modify: `trace_permission_flow.py`
- Regenerate: `WIRE_PROTOCOL.md`

- [ ] **Step 1: Replace kama references in trace_permission_flow.py**

```bash
sed -i 's/kama-core/naohua-core/g; s/kama_claude/naohua_claude/g' trace_permission_flow.py
```

- [ ] **Step 2: Regenerate WIRE_PROTOCOL.md**

```bash
uv run python scripts/gen_protocol_doc.py
```

Expected: WIRE_PROTOCOL.md regenerated with `NAOHUA_HOST` / `NAOHUA_PORT` and `naohua_claude.core.loop`

---

### Task 8: Sync dependencies and verify

**Files:**
- None (runtime)

- [ ] **Step 1: Reinstall package in dev mode**

```bash
uv sync
```

Expected: new entry points `naohua`, `naohua-core`, `naohua-tui` installed

- [ ] **Step 2: Verify entry points exist**

```bash
uv run naohua --version
uv run naohua-core --help 2>&1 | head -5
```

- [ ] **Step 3: Run unit tests**

```bash
uv run pytest tests/unit -v
```

Expected: all tests pass

- [ ] **Step 4: Run integration tests**

```bash
uv run pytest tests/integration -v
```

Expected: all tests pass

- [ ] **Step 5: Run linter**

```bash
uv run ruff check src tests scripts
```

Expected: no errors

- [ ] **Step 6: Run type checker**

```bash
uv run mypy src
```

Expected: no errors
