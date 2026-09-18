-- Persistent reflections captured during a revision session.
-- These are deliberately separate from scored attempts: a learning note is
-- evidence of reflection, not something the application should pretend to mark.

create table if not exists learning_note (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references session(id),
  topic_id uuid references topic(id),
  subtopic_id uuid references subtopic(id),
  kind text not null default 'reflection',
  content text not null,
  self_rated_confidence int check (self_rated_confidence between 1 and 5),
  misconception_tag text,
  created_at timestamptz not null default now()
);

create index if not exists idx_learning_note_created_at on learning_note(created_at desc);
create index if not exists idx_learning_note_topic_id on learning_note(topic_id);
