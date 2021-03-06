# Purpose

Steuermann is a tool to execute interdependent tasks on multiple machines.  The
main point is to define a command to run on some machine, but also to state
that it happens after some other commands that may be on that machine or other
machines.  The program "smc" analyzes the dependencies and then uses ssh (or
something similar) to execute the commands in the right order.

## The .sm file that Christine wrote
(`https://trac.assembla.com/u-rel/browser/build/trunk/steuermann/build_ur.sm`)
does not expect you to put scripts on the target machine for you.  The command
on line 4 (`build_UR/setup`) runs on every machine that you will build on; it
gets the scripts needed by using `svn export`.

It assumes a shared file system to store the source code on.  The commands on
line 9 (`build_UR/make_source_tar_urel`) and 12 (`build_UR/make_source_tar_iraf`)
create tar files of the source code.  All the other builds begin with those
source tar files.  The main point here is to have the same source code built on
all the platforms.


## Outline of a .sm file

It defines a set of commands to be executed.  Each command has a name.  The
fully qualified command name is host:tablename/commandname.  host is the
machine where the command will run.  tablename is which table the command is
part of (the table name identifies which table in the report; it helps to have
multiple tables when you have many entries, but Christine does not have many
entries yet).  commandname is a name that identifies the command.

```
TABLE tablename HOST hostlist
```

insert the following commands into table "tablename" and run them on every host
in hostlist.  TABLE is followed by one or more CMD directives.

```
CMD cmdname RUN "command string"
```

define a command named "cmdname"; to perform this command use "command string".
CMD is followed by zero or more AFTER clauses.

```
CMD cmdname LOCAL "command string"
```

define a command, but instead of running it on the designated host, run it
locally on behalf of that host.  If you use this in a table that has 5 hosts in
the hostlist, the command will run 5 times on the local machine.  It will know
which host you are running it for, so, for example, it can be a command to copy
files to that machine.

```
AFTER othercmdname
```

states that this command must be executed after othercmdname is finished.  You
can list as many AFTER clauses as you want.  Redundant `AFTER` clauses do not
hurt anything.  In an `AFTER` clause, you can use a partially qualified command
name.  `AFTER xxx` means, after command xxx for this machine finishes.  You
can also use wildcards:

`AFTER *:x/y` means after command x/y finishes on _every_ host.

`AFTER x/*` means after every command in table x finishes on this host.

`AFTER *:x/*` means after every command in table x finishes on every host.


The main reason I wrote steuermann is the complex builds I do for SSB.  I have
cross-host dependencies.  For example, I build `STSDAS` only on 32 bit machines,
then copy the result to 64 bit machines.  The interesting parts of the SM
config for that look like this:

```
TABLE build HOST herbert bond CMD dev.stsci_iraf RUN "build_stsci_iraf dev"
AFTER init/* AFTER *:assemble/dev.stsci_iraf AFTER build/dev.axe

TABLE build HOST thor arzach CMD dev.stsci_iraf_64hack RUN
"build_stsci_iraf_64hack dev herbert" AFTER herbert:build/dev.stsci_iraf*

TABLE build HOST cadeau banana CMD dev.stsci_iraf_64hack RUN
"build_stsci_iraf_64hack dev bond" AFTER bond:build/dev.stsci_iraf*
```

This means I run `herbert:build/dev.stsci_iraf` and `bond:build/dev.stsci_iraf` to
compile iraf.  After that finishes, I run `thor:build/dev.stsci_iraf_64hack` to
copy the built files to thor from `herbert`, `cadeau:build/dev.stsci_iraf_64hack`
to copy the files to `cadeau` from `bond`, etc etc.

smc understands that it can run more than one command on each machine, so it
can do this concurrently, up to the limit for concurrent tasks defined in
hosts.ini

There are bunches of other details that I'll have to describe some time.

Mark


## Host groups

The new HOSTGROUP feature works like this:

```
# defines a set of conditions - each condition is a python function in a
# CONDITIONS block
CONDITIONS 
    # for a function, the truth value is the return value
    def foo() : return True def bar() : return False

    # for anything else, it is just the value:
    baz = platform.node.endswith('.stsci.edu') END
# the END must be on a line by itself


HOSTGROUP @xyz IF foo : a1 a2 a3
        # adds a1, a2, a3 to hostgroup @xyz if condition foo() returns trun
    IF bar : b1 b2 b3
        # adds b1, b2, b3 to hostgroup @xyz if condition bar() returns trun


TABLE whatever HOST @xyz banana
    # defines table whatever to be on all the hosts in xyz and the host banana
    ...
```

In your `AFTER` clause, you can write it as

```
AFTER @xyz:this/that
```

is the same as `AFTER a1:this/that AFTER a2:this/that AFTER a3:this/that`

assuming that condition `foo()` was true and `bar()` was false


