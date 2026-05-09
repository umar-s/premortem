# premortem

A Claude Code skill that runs a structured premortem on a concrete plan,
launch, hire, or decision — finds in 10–15 minutes the holes that would
otherwise show up only after the failure.

[Russian / Русский](README.ru.md)

---

## Why this exists

You ship a product — feels well thought out. Three months later it's
dead. And the whole way through, Claude was cheerfully nodding: "yeah,
solid plan, good luck!"

That's not a bug in any specific model. It's the default behaviour of
all LLMs. Ask "what could go wrong?" and you get hedged, polite, generic
risk lists. Ask "is this a good plan?" and the model finds reasons to
say yes.

**Premortem breaks the pattern.** Not "evaluate this plan," but "imagine
the plan has already failed — explain how it died." The model switches
into narrative mode and produces concrete, creative, honest causes
instead of hedging.

Mitchell, Russo & Pennington (1989) measured ~30% more specific causes
of future outcomes under past-tense framing than under conditional
framing. Kahneman called premortem his single most valuable
decision-making tool.

This skill ports the method into Claude Code as a reproducible session
with deterministic mechanics and persistent history.

---

## What it does

The session has four phases:

- **Pre-flight** — syncs context with what the project already knows
  (CLAUDE.md, attached briefs), only asks for what's missing.
- **Silent scan** — three parallel helpers look at the plan from six
  angles (Customer, Operator, Adversary, Assumptions, situational angle,
  and always "Future Maintainer" for the WYSIATI micro-step). Semantic
  dedup leaves 5–8 unique holes.
- **Live dialog** — for each hole the skill proposes 2–3 strategic
  options, the user picks one. The top 1–3 are expanded to full mode
  (prevent / detect / stop condition / limit damage).
- **Persist** — atomic write to `docs/premortem/<plan-name>.md` plus a
  snapshot in `history/`. A month later you can re-run premortem on the
  same plan and compare: which holes closed, which got worse, which are
  new.

Built into the synthesis: outside view (Kahneman & Lovallo 2003), bias
scan with 6 items from the Kahneman/Lovallo/Sibony HBR 2011 checklist,
and a conditional reverse-premortem (Klein 2025) when the recommendation
is `delay`/`abort` — countering the over-cautious bias of pure
premortem.

---

## How it works

### Phase 1. Pre-flight (1–2 min)

The skill first scans available context — what's already in the chat or
in project files. It only asks for what's missing. Minimum to start:

- subject (what's launching / being decided)
- audience
- success criterion
- evaluation horizon (30 days / 3 months / 12 months / after pilot /
  after launch)

Reference class is asked separately: "What does this resemble from
projects already done?" — the foundation for the outside view.

### Phase 2. Silent scan (3–5 min)

The skill classifies the plan type and picks 6 angles for it. Three
**parallel LLM helpers run in one message** (2 angles each). Each
returns up to 2 holes with a confidence marker: "backed by context" /
"needs verification" / "assumption."

Hash dedup removes obvious duplicates; semantic dedup merges close holes
while preserving sources. Result: 5–8 unique holes, sorted by
importance × confidence.

The user only sees the chosen angles in one line, then the prepared
list of holes.

### Phase 3. Live dialog (5–8 min)

For each hole:

1. Description in one paragraph + why it matters + angle + confidence.
2. **2–3 strategic options** with +/–. Directions, not tasks.
3. User picks / asks for other options / defers / rejects.
4. For the chosen option: what we picked, why, first step, owner
   (agent / human / both).

After all holes:

- The skill picks the top 1–3 by importance × reversibility ×
  confidence.
- The top is expanded to full mode: prevent / detect / stop condition /
  limit damage.
- **Bias check on the top.** The skill proposes the most likely
  cognitive bias that may have distorted the decisions, and a concrete
  correction.
- **Session recommendation:** `continue` / `reduce_stake` / `delay` /
  `abort` — based on the pattern of accepted decisions.
- **Reverse premortem** runs only on `reduce_stake` / `delay` /
  `abort`: "the horizon passed. We didn't do it. Turned out to be a
  mistake — why?" Counter to the over-cautious pull of pure premortem.

### Phase 4. Persist (1 min)

One main file at `docs/premortem/<slug>.md` plus a timestamped snapshot
in `docs/premortem/history/`. Writes are atomic (tempfile + os.replace
+ fsync) under an advisory file lock. Any sequence of runs leaves the
file valid.

---

## What you get

A single markdown file with YAML frontmatter:

- **Context:** subject / audience / success / horizon / reference class
- **Holes** (5–8): id, title, angle, importance, confidence, status,
  description, accepted decision
- **Top 1–3** holes in full mode: prevent / detect / stop / limit
  damage, owner, first step
- **Bias check** in one line
- **Session recommendation** + reason
- **Reverse premortem** (when applicable): 3 reasons "why we may have
  been wrong not to do it" + what tips the balance
- **Run history** with status dynamics: `same` / `worse` / `resolved` /
  `new`

---

## When to use

The skill works on concrete, reversible commitments with a high cost of
being wrong. Good cases:

- **Product / feature launch.** "Shipping the new dashboard in 6
  weeks."
- **Pricing change.** "Bumping the subscription from $19 to $39."
- **Hire.** "First marketing hire, junior, $60k base."
- **Content launch.** "$297 live workshop on [topic] for [audience]."
- **Architecture decision.** "Migrating monolith to microservices in a
  quarter."
- **Partnership / contract.** "Signing a 12-month exclusive with one
  distribution channel."

Minimum requirements: there's a plan with shape (not an idea in your
head), you have 10–15 minutes, the commitment isn't finalized yet.

---

## When NOT to use

- **Idea without shape.** Nothing to break — help draft the plan first,
  then premortem.
- **Question with one right answer.** "Which model is faster?" — that's
  fact-check, not premortem.
- **Creative editing of a draft.** That's editing, not premortem.
- **Already-irreversible decision.** Premortem can't roll it back.
- **Multi-perspective input on a present-tense decision.** LLM Council
  pattern fits better than past-tense framing.

---

## Recommendations

- **Run when the plan is "almost ready."** Too early — nothing to
  break. Too late — you can't influence anything.
- **Don't skip reference class.** "What does this resemble from done
  projects?" is the cheapest source of outside view. If you don't know
  — say so, the skill moves on with empty reference class.
- **Don't default to "defer."** Premortem systematically biases toward
  caution (Klein 2025). That's why reverse-premortem is built in: it
  asks "what if we were wrong NOT to do it?"
- **Re-run after a month.** History compares — which holes closed,
  which got worse, which are new. Catches plan drift.
- **Don't run premortem on someone else's plan without context.** Get
  at least subject / audience / success first. Without that you'll get
  a generic risk checklist, not premortem.
- **Accept 2–3 decisions, not 8.** If the skill produces 8 holes and
  you accept all of them, it's likely an illusion of control.
  Premortem worked when the top is chosen and there's a concrete first
  step.

---

## Installation

**Requirements:**
- Claude Code
- Git
- [uv](https://docs.astral.sh/uv/) — runs the CLI scripts
  (deterministic mechanics)

**Install:**

```bash
git clone https://github.com/AndyShaman/premortem.git
cd premortem
./install.sh
```

The installer copies `premortem/` (SKILL.md, scripts, references,
assets, evals) to `~/.claude/skills/premortem/`. Tests stay in the
repo.

**Verify:**

```bash
ls ~/.claude/skills/premortem/SKILL.md
```

Restart Claude Code (or start a new session) — the skill loads
automatically on trigger phrases.

**Update:**

```bash
cd premortem
git pull
./install.sh
```

---

## Triggers

The skill auto-loads on phrases like:

- "premortem", "premortem this", "run premortem"
- "find holes in this plan"
- "look at this plan from the outside"
- "what could kill this [plan]?"
- "what am I missing in [plan]"
- "future-proof this [plan/launch]"

Example prompts:

- "premortem this: launching a $297 live workshop on Claude Cowork for
  marketing teams"
- "stress-test this hire — first marketing person, junior, $60k base"
- "find holes — shipping the new pricing in 2 weeks"

---

## Method origins

- Gary Klein, *Performing a Project Premortem*, HBR, 2007
- Klein, *Sources of Power*, MIT Press, 1998 — mental simulation, RPD
- Klein, *The Pre-Mortem Method*, Psychology Today, 2021 — action round
- Klein, *Double-Barreled Pre-Mortems*, Psychology Today, 2025 —
  reverse premortem
- Mitchell, Russo & Pennington, *Back to the Future: Temporal
  Perspective in the Explanation of Events*, JBDM, 1989 — prospective
  hindsight
- Veinott, Klein & Wiggins, *Evaluating the Effectiveness of the
  PreMortem Technique*, ISCRAM, 2010 — empirical validation
- Kahneman, *Thinking, Fast and Slow*, 2011, ch. 23–24
- Kahneman & Lovallo, *Delusions of Success*, HBR, 2003 — outside view
- Kahneman, Lovallo & Sibony, *Before You Make That Big Decision*, HBR,
  2011 — 12-question bias checklist (6 items adopted in synthesis)

---

## License

MIT — see [LICENSE](LICENSE).
