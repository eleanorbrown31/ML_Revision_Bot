# ML Revision Engine — Build Specification

**Purpose:** A self-hosted revision system for a Level 7 AI & Data Science apprenticeship EPA. Persistent attainment tracking, adaptive question selection, editable curriculum, phone-first access.

**Status:** Planning document. Intended as the brief for a Claude Code build.

---

## 1. Headline decisions

| Concern | Decision | Why |
|---|---|---|
| Interface | Streamlit, deployed to Streamlit Community Cloud | Already familiar; Claude Code writes it quickly; works on phone via browser |
| Database | Supabase Postgres (already provisioned) | Proper persistence, cross-device, free tier is ample |
| LLM access | OpenRouter, single key, different models per job | One billing surface, easy model swaps |
| Question supply | Pre-generated **question bank**, topped up in batches | Reviewable, retirable, reusable, fast at quiz time |
| Marking | Live LLM call against a stored **rubric** | Rubric-anchored marking is what kills sycophancy |
| Auth | Passcode in `st.secrets` (single user) | Community Cloud apps are public URLs; this is enough for one user |

The two decisions doing the real work here are the question bank and the rubric. Everything else is plumbing.

---

## 2. Architecture

```
Phone / laptop browser
        │
   Streamlit app (Community Cloud)
        │
        ├── Supabase Postgres  ← all state, all history
        │
        └── OpenRouter
              ├── generation   (stronger model, batch/offline)
              └── readings     (batch/offline, cached)
```

**Marking is local Python.** First iteration uses objective formats only — multiple choice, multi-select, fill-in-the-blank, matching, ordering, numeric entry. All of these are markable against a stored answer key without an LLM. That means no model call sits on the critical path: quiz responses are instant, work on poor signal, and cost nothing.

No agent orchestration framework. This does not need one. It needs two prompt templates, a scheduler function, and a well-shaped database. Multi-agent adds failure modes and latency without adding pedagogy.

**Connection note:** use Supabase's transaction pooler (port 6543) rather than a direct connection — Streamlit reruns the script on every interaction and will exhaust direct connections. Cache the client with `@st.cache_resource`.

---

## 3. Data model

Principles, applied without exception:

1. UUID primary keys everywhere. No natural keys, no auto-increment integers exposed in logic.
2. Curriculum nodes are **soft-deleted** (`is_active = false`). Nothing in the curriculum tree is ever `DELETE`d.
3. Attempts store both a foreign key *and* a text snapshot of what was asked. Renaming a topic must not rewrite history.
4. Prompts are versioned rows, not code constants.

### Curriculum tables

```sql
area (
  id uuid pk, name text, sort_order int,
  is_active bool default true, created_at timestamptz
)

topic (
  id uuid pk, area_id uuid fk → area,
  name text, description text,
  exam_weight numeric default 1.0,   -- how heavily EPA leans on this
  is_active bool default true, created_at timestamptz
)

subtopic (
  id uuid pk, topic_id uuid fk → topic,
  name text,
  learning_objectives jsonb,          -- ["state the loss function", "explain why convex", ...]
  is_active bool default true, created_at timestamptz
)
```

Subtopic is the unit of mastery and scheduling. Topic is for grouping and reporting. Area is for interleaving constraints.

### Lineage — the bit that protects your records

```sql
curriculum_lineage (
  id uuid pk,
  from_node_id uuid, to_node_id uuid,
  node_type text,                     -- 'subtopic' | 'topic'
  kind text,                          -- 'split' | 'merge' | 'rename' | 'move'
  weight numeric default 1.0,
  created_at timestamptz
)
```

This lets curriculum restructuring be a first-class operation rather than data loss:

- **Rename** — update `name`. Attempts keep their snapshot text. Mastery untouched. No lineage row needed unless you want the audit trail.
- **Move** a subtopic to a different topic — update `topic_id`. Mastery is keyed on `subtopic_id`, so it follows the subtopic automatically.
- **Split** A into B and C — insert B and C, set A `is_active = false`, write two lineage rows with `kind='split'`. Initialise B and C ability from A's ability, discounted (suggest ×0.9 — you demonstrably knew *something*, but not necessarily the part now isolated).
- **Merge** A and B into C — insert C, deactivate A and B, two lineage rows with `kind='merge'`. C's ability is the attempt-count-weighted mean of A and B.

Progress charts then offer a "include predecessors" toggle that walks the lineage graph. Nothing is ever silently orphaned.

### Question bank

```sql
question (
  id uuid pk, subtopic_id uuid fk → subtopic,
  difficulty text,                    -- 'F1' | 'F2' | 'F3' | 'INT' | 'ADV'
  format text,                        -- 'mcq' | 'multi' | 'fill' | 'match' | 'order' | 'numeric'
  stem text,
  payload jsonb,                      -- options / pairs / blanks / sequence, format-dependent
  answer_key jsonb,                   -- format-specific; see §5
  explanation text,                   -- written at generation time, shown after marking
  distractor_notes jsonb,             -- optional: why each wrong option is wrong
  status text default 'draft',        -- 'draft' | 'active' | 'retired'
  source text,                        -- 'llm' | 'authored'
  generator_prompt_version_id uuid fk → prompt_version,
  generator_model text,
  created_at timestamptz
)
```

`status` means a bad question gets retired, never deleted, and every attempt against it stays interpretable.

### Attempts and mastery

```sql
attempt (
  id uuid pk, session_id uuid fk → session,
  question_id uuid fk → question,
  subtopic_id uuid,                   -- denormalised for fast querying
  area_name_snapshot text,
  topic_name_snapshot text,
  subtopic_name_snapshot text,
  difficulty text,
  question_stem_snapshot text,
  response text,
  score numeric,                      -- 0.0–1.0
  rubric_points_hit jsonb,
  critique text,
  self_rated_confidence int,          -- 1–5, captured before marking
  seconds_taken int,
  hint_used bool default false,
  marker_prompt_version_id uuid fk → prompt_version,
  marker_model text,
  created_at timestamptz
)

mastery (
  subtopic_id uuid pk fk → subtopic,
  ability numeric default 0,          -- 0–100
  current_band text default 'F1',
  attempts_count int default 0,
  consecutive_strong int default 0,
  consecutive_weak int default 0,
  last_seen_at timestamptz,
  next_due_at timestamptz,
  interval_days numeric default 1,
  ease numeric default 2.5
)

session (
  id uuid pk, mode text, config jsonb,
  started_at timestamptz, ended_at timestamptz
)

bookmark (id uuid pk, subtopic_id uuid, question_id uuid, note text, created_at timestamptz)
```

### Prompt versioning

```sql
prompt_version (
  id uuid pk,
  role text,                          -- 'generator' | 'marker' | 'reading'
  body text,
  notes text,                         -- what you changed and why
  is_active bool default false,
  created_at timestamptz
)
```

Refining the questioning = inserting a new row and flipping `is_active`. Old attempts keep pointing at the old version.

This matters more than it looks. If you tighten the marker prompt and your scores drop ten points, that is a marking change, not a competence change. Being able to filter attempts by `marker_prompt_version_id` is the only way to tell those apart. Consider drawing a vertical line on progress charts wherever the active marker version changed.

---

## 4. Mastery and scheduling

### Ability update

Exponentially weighted moving average, difficulty-weighted:

```
band_weight = {F1: 0.6, F2: 0.8, F3: 1.0, INT: 1.3, ADV: 1.6}
raw         = score × band_weight[difficulty] × 100
ability_new = clamp(0, 100, (1 - α)·ability_old + α·raw)   with α = 0.3
```

Cap `raw` at 100 so a single strong advanced answer cannot max out a subtopic.

### Band progression

- Promote when `consecutive_strong >= 3` (strong = score ≥ 0.8) and `attempts_count >= 5` at the band.
- Demote when `consecutive_weak >= 2` (weak = score < 0.5).
- Never promote past ADV; never demote below F1.

### Spaced repetition

SM-2 variant on the subtopic:

```
if score >= 0.8:  ease += 0.10;  interval ×= ease
elif score >= 0.5: interval ×= 1.2
else:              ease -= 0.20;  interval = 1
ease clamped to [1.3, 2.8];  interval clamped to [1, 21] days
next_due_at = now + interval_days
```

Interval cap of 21 days is deliberate — with a fixed exam date you cannot afford a six-month interval on anything.

### Question selection

Score every active subtopic, take the top N with constraints:

```
priority = 0.40 × overdue_norm            -- days past due / 7, capped at 1
         + 0.30 × (1 − ability/100)
         + 0.15 × coverage_gap            -- 1 if never attempted, decaying with attempts
         + 0.10 × exam_weight_norm
         + 0.05 × random()
```

**Interleaving constraints**, applied after scoring:

- No more than two consecutive questions from the same topic.
- A session of ≥8 questions must touch at least three areas.
- At least one question per session from a subtopic last seen >14 days ago, if one exists.

**Timetable pressure:** as the exam date approaches, shift the weights — raise `coverage_gap` early (breadth first), raise `overdue_norm` and `1−ability` later (shore up weak spots). A single `days_to_exam` parameter interpolating between two weight vectors is enough. Don't build a calendar; build a weighting.

---

## 5. Marking

Deterministic, in Python. No model involved.

| Format | `payload` | `answer_key` | Scoring |
|---|---|---|---|
| `mcq` | `{options: [...]}` | `{correct: 2}` | 1 or 0 |
| `multi` | `{options: [...]}` | `{correct: [0,3]}` | Jaccard: `hits / (correct ∪ selected)` |
| `fill` | `{template: "The ___ measures ___"}` | `{blanks: [["gini","gini impurity"], ["impurity"]]}` | Fraction of blanks correct; accepts any listed synonym |
| `match` | `{left: [...], right: [...]}` | `{pairs: {"L1":"R3", ...}}` | Fraction of pairs correct, keyed on **text** not index |
| `order` | `{items: [...]}` | `{sequence: [2,0,1,3]}` | Kendall tau normalised to 0–1, so near-misses score partial |
| `numeric` | `{prompt, unit}` | `{value: 0.48, tolerance: 0.01}` | 1 or 0 within tolerance |

Rules:
- Text comparison is case-insensitive, whitespace-normalised, and punctuation-stripped. Never penalise spelling — use fuzzy matching (Levenshtein distance ≤ 2 on tokens over 4 characters) against the synonym list.
- Present the stored `explanation` after every question, right or wrong. It was written once at generation time, so it is identical every time you see that question — which is a feature for retention.
- No praise strings anywhere in the UI. Correct/incorrect, the explanation, the score. Nothing else.
- Hints only on explicit request, and only if `distractor_notes` exists; log `hint_used = true` and apply a 0.5 multiplier.

Sycophancy is now impossible by construction — there is no model deciding how you did.

**Deferred to v2:** free-text answers with LLM rubric marking. When that lands, add `rubric jsonb` back onto `question`, and a marker prompt that is given the rubric points and returns only which were hit, with the score computed in Python from the weights. The model must never be asked "how did she do?".

---

## 6. App structure

Streamlit pages, kept deliberately thin:

1. **Quiz** — one question per screen. Big touch targets. Confidence slider before submit. Mark → feedback → next. This is the only page that needs to be excellent on a phone.
2. **Dashboard** — ability by area and topic, due-today count, attempts over time, weakest ten subtopics.
3. **Curriculum** — CRUD over area/topic/subtopic. Rename, move, split, merge, deactivate. Every destructive-looking action writes lineage rows and shows what will happen to existing records before confirming.
4. **Question bank** — browse, filter, edit, retire. Manually author questions. Trigger batch generation for a subtopic/difficulty.
5. **Prompts** — view and edit generator/marker/reading prompts; activate a version; see which versions are in use historically.
6. **Readings** — "Learn First" mode: generate and cache a revision reading per subtopic, then quiz.
7. **Export** — download everything as JSON. One button.

**Mobile realities.** Streamlit is usable on a phone but not native-feeling. Collapse the sidebar by default. Avoid multi-column layouts on the quiz page. Use `st.radio` and `st.button` over anything requiring precise tapping. "Add to Home Screen" gets you a chrome-less icon that feels app-ish. If this ends up too clunky, the escape hatch is a FastAPI + HTMX PWA, but try Streamlit first — you know it and the build cost is much lower.

---

## 7. Rules for Claude Code

State these explicitly in the brief. They matter more than any feature.

1. **Never** `DROP TABLE`, `DROP COLUMN`, or `DELETE FROM` on curriculum, question, attempt or mastery tables. Additive migrations only.
2. All schema changes go in numbered migration files under `/migrations`, applied in order, each idempotent.
3. Soft-delete via `is_active`; the UI never offers a hard delete.
4. Any curriculum restructure writes `curriculum_lineage` rows in the same transaction.
5. Secrets in `st.secrets` / Streamlit Cloud settings. Never in the repo.
6. Every OpenRouter call is wrapped in try/except with a visible, non-fatal error; a failed marking call must not lose the typed response — persist the attempt with `score = null` and allow re-marking.
7. Write a seed script that imports the existing `localStorage` JSON export from the current artefact so prior progress is carried over, not restarted.
8. Reconcile with the Supabase tables already created (`topic_scores`, `session_history`, `revision_schedule`, `bookmarks`, `topic_summary`) — if empty, replace them with this schema in a migration rather than working around them.

---

## 8. Build order

Get to a usable quiz fast, then deepen.

1. Schema + migrations + seed the 37 topics into the area/topic/subtopic tree.
2. Supabase client, connection pooling, passcode gate.
3. Question bank table + a manual authoring form. Author twenty questions by hand across three subtopics.
4. Quiz page: select → serve → answer → mark → persist. Ability and SR updates.
5. Dashboard.
6. Batch generation into the bank, with a review queue (`draft` → `active`).
7. Curriculum editor with lineage.
8. Prompt versioning UI.
9. Readings / Learn First.
10. Export.

Steps 1–5 are the actual product. Everything after is refinement.

---

## 9. Open questions

- **Voice input.** Streamlit's `st.audio_input` captures audio, but OpenRouter is chat-focused and its transcription support needs checking before you rely on it. You may need a separate transcription provider (Groq, Deepgram, OpenAI direct). Worth confirming before committing to voice in v1 — and worth asking whether typed answers are actually better practice for a written EPA.
- **Model choice.** Suggest a strong model for generation (quality is worth paying for, it's offline and batched) and a fast cheap one for marking. Log the model on every attempt so you can compare.
- **Exam date.** The scheduler wants a `days_to_exam` value. Set it once in config.
- **Recognition versus recall.** Objective formats measure recognition, which reliably overstates what you can produce unprompted. For a written EPA and a professional discussion, that gap matters. Mitigations within objective formats: lean on `fill`, `order` and `numeric`, which are closer to recall than `mcq`. Then plan free-text as v2 and treat v1 scores as an upper bound on real competence.
- **Mastery unit.** The spec above keys mastery on subtopic. With ~270 subtopics that means each is seen rarely. Consider keying mastery on **topic** (53 nodes) and using subtopic purely as a coverage tag on questions, so the scheduler ensures you meet every subtopic within a topic without fragmenting the ability estimate.
