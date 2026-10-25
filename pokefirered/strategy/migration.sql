CREATE TABLE strategy_version(version INTEGER NOT NULL,configuration_sha TEXT NOT NULL);
CREATE TABLE strategy_log(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT NOT NULL UNIQUE,campaign TEXT NOT NULL,branch TEXT NOT NULL,cursor INTEGER NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE strategy_branches(branch TEXT PRIMARY KEY REFERENCES branches(id),parent_cutoff INTEGER NOT NULL);
CREATE TABLE strategy_view(campaign TEXT PRIMARY KEY REFERENCES campaigns(id),branch TEXT NOT NULL,cutoff INTEGER NOT NULL,epoch INTEGER NOT NULL);
CREATE TABLE strategy_checkpoints(checkpoint TEXT PRIMARY KEY REFERENCES checkpoints(id),cutoff INTEGER NOT NULL,state_sha TEXT NOT NULL);
CREATE TABLE strategy_jobs(id TEXT PRIMARY KEY,context TEXT NOT NULL,status TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,outcome TEXT);
