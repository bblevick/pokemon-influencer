CREATE TABLE social_version(version INTEGER PRIMARY KEY CHECK(version=1), reducer INTEGER NOT NULL, config_sha TEXT NOT NULL);
CREATE TABLE social_log(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE NOT NULL,campaign TEXT NOT NULL REFERENCES campaigns(id),branch TEXT NOT NULL REFERENCES branches(id),cursor INTEGER NOT NULL,kind TEXT NOT NULL,semantic_key TEXT NOT NULL,payload TEXT NOT NULL,UNIQUE(branch,kind,semantic_key));
CREATE TABLE social_view(campaign TEXT PRIMARY KEY REFERENCES campaigns(id),branch TEXT NOT NULL,cutoff INTEGER NOT NULL,epoch INTEGER NOT NULL);
CREATE TABLE social_branches(branch TEXT PRIMARY KEY REFERENCES branches(id),parent_cutoff INTEGER NOT NULL);
CREATE TABLE social_checkpoints(checkpoint TEXT PRIMARY KEY REFERENCES checkpoints(id),cutoff INTEGER NOT NULL,state_sha TEXT NOT NULL);
