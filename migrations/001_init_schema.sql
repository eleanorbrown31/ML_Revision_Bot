-- Full schema for the ML Revision Engine.
-- Idempotent: every statement is safe to re-run.
--
-- Deviations from revision-engine-build-spec.md §3 (see build plan for rationale):
--   * mastery is keyed on topic_id, not subtopic_id (mastery tracked at topic level).
--   * attempt carries an added topic_id column (denormalised, alongside subtopic_id)
--     since mastery/dashboard/scheduler queries now group by topic.
--   * a new config table holds editable settings (currently just exam_date).

-- --- Curriculum tree ---------------------------------------------------------

create table if not exists area (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  sort_order int not null default 0,
  is_active bool not null default true,
  created_at timestamptz not null default now()
);

create table if not exists topic (
  id uuid primary key default gen_random_uuid(),
  area_id uuid not null references area(id),
  name text not null,
  description text,
  exam_weight numeric not null default 1.0,
  is_active bool not null default true,
  created_at timestamptz not null default now()
);

create table if not exists subtopic (
  id uuid primary key default gen_random_uuid(),
  topic_id uuid not null references topic(id),
  name text not null,
  learning_objectives jsonb,
  is_active bool not null default true,
  created_at timestamptz not null default now()
);

create table if not exists curriculum_lineage (
  id uuid primary key default gen_random_uuid(),
  from_node_id uuid not null,
  to_node_id uuid not null,
  node_type text not null,   -- 'subtopic' | 'topic'
  kind text not null,        -- 'split' | 'merge' | 'rename' | 'move'
  weight numeric not null default 1.0,
  created_at timestamptz not null default now()
);

-- --- Prompt versioning (created before question, which references it) -------

create table if not exists prompt_version (
  id uuid primary key default gen_random_uuid(),
  role text not null,        -- 'generator' | 'marker' | 'reading'
  body text not null,
  notes text,
  is_active bool not null default false,
  created_at timestamptz not null default now()
);

-- --- Question bank ------------------------------------------------------------

create table if not exists question (
  id uuid primary key default gen_random_uuid(),
  subtopic_id uuid not null references subtopic(id),
  difficulty text not null,   -- 'F1' | 'F2' | 'F3' | 'INT' | 'ADV'
  format text not null,       -- 'mcq' | 'multi' | 'fill' | 'match' | 'order' | 'numeric'
  stem text not null,
  payload jsonb not null,
  answer_key jsonb not null,
  explanation text not null,
  distractor_notes jsonb,
  status text not null default 'draft',  -- 'draft' | 'active' | 'retired'
  source text not null default 'authored',  -- 'llm' | 'authored'
  generator_prompt_version_id uuid references prompt_version(id),
  generator_model text,
  created_at timestamptz not null default now()
);

-- --- Sessions, mastery, attempts ---------------------------------------------

create table if not exists session (
  id uuid primary key default gen_random_uuid(),
  mode text not null,
  config jsonb,
  started_at timestamptz not null default now(),
  ended_at timestamptz
);

create table if not exists mastery (
  topic_id uuid primary key references topic(id),
  ability numeric not null default 0,
  current_band text not null default 'F1',
  attempts_count int not null default 0,
  consecutive_strong int not null default 0,
  consecutive_weak int not null default 0,
  last_seen_at timestamptz,
  next_due_at timestamptz,
  interval_days numeric not null default 1,
  ease numeric not null default 2.5
);

create table if not exists attempt (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references session(id),
  question_id uuid not null references question(id),
  subtopic_id uuid not null,
  topic_id uuid not null,
  area_name_snapshot text not null,
  topic_name_snapshot text not null,
  subtopic_name_snapshot text not null,
  difficulty text not null,
  question_stem_snapshot text not null,
  response text,
  score numeric,
  rubric_points_hit jsonb,
  critique text,
  self_rated_confidence int,
  seconds_taken int,
  hint_used bool not null default false,
  marker_prompt_version_id uuid references prompt_version(id),
  marker_model text,
  created_at timestamptz not null default now()
);

create table if not exists bookmark (
  id uuid primary key default gen_random_uuid(),
  subtopic_id uuid,
  question_id uuid,
  note text,
  created_at timestamptz not null default now()
);

-- --- Config -------------------------------------------------------------------

create table if not exists config (
  key text primary key,
  value jsonb not null,
  updated_at timestamptz not null default now()
);

insert into config (key, value)
values ('exam_date', 'null'::jsonb)
on conflict (key) do nothing;

-- --- Indexes --------------------------------------------------------------

create index if not exists idx_topic_area_id on topic(area_id);
create index if not exists idx_subtopic_topic_id on subtopic(topic_id);
create index if not exists idx_question_subtopic_status on question(subtopic_id, status);
create index if not exists idx_attempt_session_id on attempt(session_id);
create index if not exists idx_attempt_question_id on attempt(question_id);
create index if not exists idx_attempt_topic_id on attempt(topic_id);
create index if not exists idx_attempt_subtopic_id on attempt(subtopic_id);
create index if not exists idx_mastery_next_due_at on mastery(next_due_at);
create index if not exists idx_curriculum_lineage_from on curriculum_lineage(from_node_id);
create index if not exists idx_curriculum_lineage_to on curriculum_lineage(to_node_id);
