# Runbook: Onboarding checklist

First-week checklist for engineers joining the Maui team. Tick items off as you go;
the order matters where dependencies exist. If you can't complete an item, raise it
with the data lead before moving on.

## Day 1 — access and orientation

- [ ] **GitHub access to `beyondessential` org.** Confirm via
      <https://github.com/beyondessential> showing private repos. Request from IT
      via the data lead if missing.
- [ ] **Read the team intro.** Start with [`AGENT.base.md`](AGENT.base.md) for the
      shared context, then [`architecture/data-architecture.md`](architecture/data-architecture.md)
      for the north star, then [`glossary.md`](glossary.md) when terms aren't clear.
- [ ] **Slack / team channel access.** Confirm you can see the Maui team channel
      and have introduced yourself.
- [ ] **Linear access.** Request access to the Maui project. See
      [`standards/linear-conventions.md`](standards/linear-conventions.md) for
      how the team uses issues.
- [ ] **Identify your buddy / onboarding partner.** Data lead assigns one.

## Day 1–2 — local environment

- [ ] **Install [uv](https://docs.astral.sh/uv/).** Verify with `uv --version`.
- [ ] **Install Git.** Verify with `git --version`.
- [ ] **Install a Claude / AI editor.** Choose one:
  - [Claude Code](https://docs.claude.com/claude-code) (CLI + IDE extension)
  - [Cursor](https://www.cursor.com/)
  - [Codex CLI](https://github.com/openai/codex) or another tool
- [ ] **Install PostgreSQL client tools.** `psql` for ad-hoc queries; optional
      GUI (DBeaver, TablePlus).
- [ ] **Get your `ANTHROPIC_API_KEY`** (if using Claude Code locally). See
      [`environment-and-credentials.md`](environment-and-credentials.md).
- [ ] **Request database credentials** for the Tamanu replica(s) you'll work on.
      See `environment-and-credentials.md` — the data lead routes the request.

## Day 2–3 — clone a repo and set up

Pick the repo your first task lives in. Most commonly `tamanu-source-dbt` or one of
the `tamanu-dbt-<deployment>` repos.

- [ ] **Clone with submodules.**
      ```bash
      git clone --recurse-submodules <repo-url>
      ```
      Or, if you forgot `--recurse-submodules`, run `git submodule update --init`
      after cloning.
- [ ] **Verify the `.maui` symlink targets resolve.** From the repo root:
      ```bash
      cat .sqlfluff  # should be a symlink target like .maui/.sqlfluff
      ls .maui/      # should list AGENT.base.md, runbooks/, standards/, …
      ```
      If `.sqlfluff` is empty or `.maui/` is empty, your submodule didn't init.
- [ ] **Follow [`tamanu-dbt-setup.md`](tamanu-dbt-setup.md)** (or the analogous
      runbook for your repo) end-to-end. `dbt debug` should succeed before you
      stop.
- [ ] **Set up your local AI context file.** Create `CLAUDE.md` (Claude Code) or
      `.cursorrules` (Cursor) at the repo root containing `@./AGENT.md`. Add the
      file to your `.gitignore` if it isn't already — it's per-developer.
- [ ] **Set up the shared skills symlink** (Claude Code only):
      ```bash
      mkdir -p .claude
      # macOS/Linux:
      ln -s ../.maui/skills .claude/skills
      # Windows (Developer Mode or admin):
      mklink /D .claude\skills .maui\skills
      ```

## Day 3–5 — your first PR

- [ ] **Pick a small first task.** The data lead will assign one (typically a small
      doc fix, a test addition, or a model column documentation pass).
- [ ] **Read the standards relevant to your task** — at minimum
      [`standards/git-conventions.md`](standards/git-conventions.md),
      [`standards/dbt-conventions.md`](standards/dbt-conventions.md) for dbt work,
      [`standards/python-conventions.md`](standards/python-conventions.md) for
      scripts. See `README.md` at the repo root for the import list per repo type.
- [ ] **Author a spec if the task warrants one.** See
      [`standards/sdd-conventions.md`](standards/sdd-conventions.md) — non-trivial
      models, pipelines, and migrations get a spec. Trivial fixes don't.
- [ ] **Branch and commit per conventions.**
      [`standards/git-conventions.md`](standards/git-conventions.md) covers
      branch naming, commit message format, and version-branch rules.
- [ ] **Open the PR.** Pull-request template auto-populates the body; complete the
      summary and test plan. Claude Code review will run automatically; address any
      blockers before requesting human review.

## Week 2 — broader context

- [ ] **Read all `knowledge/standards/` files** at least once. Skim where
      irrelevant to your immediate work; come back as needed.
- [ ] **Read all `knowledge/runbooks/`.** These are operational; you'll reference
      them when doing the specific tasks they cover.
- [ ] **Skim the open Phase 0 items in
      [`architecture/data-architecture.md`](architecture/data-architecture.md).**
      They describe the team's current direction of travel.
- [ ] **Pair with a teammate on a real piece of work** — code review or
      collaborative model authoring.

## Anytime — if something is unclear

- The [`glossary.md`](glossary.md) covers terminology.
- The [`README.md`](README.md) at the repo root explains where each kind of
  document lives.
- For specific operational questions, search `runbooks/`; for *why* questions,
  search `architecture/`; for *what's the rule* questions, search `standards/`.
- For anything still missing, ask in the team channel and update the docs after
  you have the answer — the next person onboarding will thank you.
