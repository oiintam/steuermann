-- The table 'status' contains a record for each command in a run.
-- Before we start running anything, we insert a record for every
-- command in the test run.  The initial status is 'S'.

CREATE TABLE sm_status (
	run	VARCHAR(100),
		-- name of this run

	host	VARCHAR,
	tablename VARCHAR,
	cmd	VARCHAR,
		-- name of the command (node)

	depth	INTEGER,
		-- depth in the tree of this node (used to create report tables)

	status	VARCHAR(5),
		-- N = not started
		-- R = started, not finished
		-- S = skipped
		-- P = prereq not satisfied, so not attempted
		-- E = error internal to steuermann
		-- 0-255 = exit code

	start_time	VARCHAR(30),
	end_time	VARCHAR(30),
		-- times initially blank
		-- YYYY-MM-DD HH:MM:SS.SSS
		-- (space for resolution to nanosecond is a bit extreme)

	-- a log file name is implicit in the run/host/tablename/cmd tuple

	notes	VARCHAR(1000),
		-- notes reported by the script

    logs    INTEGER,

	FOREIGN KEY(run) REFERENCES runs(run)
		-- run name has to be in the run table
	);


create unique index sm_status_idx1 on sm_status ( run, host, tablename, cmd );


-- table lists all run names in the system
CREATE TABLE sm_runs (
	run		VARCHAR(100),
	create_time	VARCHAR(26),
	errors		int
	);

CREATE UNIQUE INDEX sm_runs_idx1 ON sm_runs(run);


-- table lists scheduled cron events - sort of like the old sr
-- 	smcron name script
CREATE TABLE sm_crons (
	host		VARCHAR,
		-- what host we ran this on
	name		VARCHAR(100),
		-- a descriptive name, not necessarily unique
	decollision	VARCHAR(10),
		-- a cookie to make (host,name,decollision) unique
	start_time	VARCHAR(30),
	end_time	VARCHAR(30),
	duration	REAL,
		-- 
	status		VARCHAR(5),
		-- exit status 
	logfile		VARCHAR(1000)
		-- log file name, relative to config logdir+'/cron/'
	);

CREATE INDEX sm_crons_idx1 ON sm_crons( host, name, decollision );

