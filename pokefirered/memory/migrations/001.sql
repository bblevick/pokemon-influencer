CREATE TABLE memory_version(version INTEGER PRIMARY KEY CHECK(version=1), reducer INTEGER NOT NULL);
INSERT INTO memory_version VALUES(1,1);
CREATE TABLE memory_actors(id TEXT PRIMARY KEY, world_trainer TEXT UNIQUE NOT NULL);
CREATE TABLE memory_sources(kind TEXT NOT NULL, id TEXT NOT NULL, PRIMARY KEY(kind,id));
CREATE TABLE memory_evidence(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE NOT NULL,
 campaign TEXT NOT NULL REFERENCES campaigns(id),branch TEXT NOT NULL REFERENCES branches(id),cursor INTEGER NOT NULL,
 actor TEXT NOT NULL REFERENCES memory_actors(id),mode TEXT NOT NULL CHECK(mode IN ('direct','delivered')),
 claim TEXT NOT NULL,source_kind TEXT NOT NULL,source_id TEXT NOT NULL,battle TEXT NOT NULL,turn INTEGER NOT NULL,
 sender TEXT REFERENCES memory_actors(id),parent TEXT REFERENCES memory_evidence(id),channel TEXT,
 status TEXT NOT NULL CHECK(status='recorded'),schema INTEGER NOT NULL CHECK(schema=1),created_at REAL NOT NULL);
CREATE INDEX memory_actor_scope ON memory_evidence(actor,branch,cursor,seq);
CREATE TABLE memory_branches(branch TEXT PRIMARY KEY REFERENCES branches(id),parent_cutoff INTEGER NOT NULL);
CREATE TABLE memory_view(campaign TEXT PRIMARY KEY REFERENCES campaigns(id),branch TEXT NOT NULL,cutoff INTEGER NOT NULL);
CREATE TABLE memory_checkpoints(checkpoint TEXT PRIMARY KEY REFERENCES checkpoints(id),cutoff INTEGER NOT NULL);
