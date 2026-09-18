-- "Learn First" readings: one cached revision reading per topic.
-- Idempotent: safe to re-run.
--
-- Keyed on topic_id (not subtopic_id) for the same reason mastery is:
-- topic is the system's unit of granularity, and 57 readings is already a
-- meaningful amount of content to author -- 270 subtopic-level readings
-- would not be.

create table if not exists reading (
  topic_id uuid primary key references topic(id),
  content text not null,
  source text not null default 'llm',
  generator_model text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
