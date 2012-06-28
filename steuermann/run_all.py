'''
run everything in a set of command files
 
'''

import time
import sys
import os.path
import datetime

import run
import report
import nodes
import getpass

import steuermann.config

import pandokia.helpers.easyargs as easyargs
import pandokia.text_table as text_table


try :
    import readline
except ImportError :
    readline = None


username=getpass.getuser()

#####

def main() :
    global xnodes
    global no_run
    # read all the input files
    
    if readline :
        history = os.path.join(os.path.expanduser("~"), ".steuermann_history")
        try :
            readline.read_history_file(history)
        except IOError :
            pass
        import atexit
        atexit.register(readline.write_history_file, history)


# easyargs spec definition:
#
#        '-v' : '',              # arg takes no parameter, opt['-v'] is
#                                # how many times it occurred
#        '-f' : '=',             # arg takes a parameter
#        '-mf' : '=+',           # arg takes a parameter, may be specified 
#                                # several times to get a list
#        '--verbose' : '-v',     # arg is an alias for some other arg

    opt, args = easyargs.get( { 
        '--all' : '-a'      ,
        '-a'    : ''        ,   # run all nodes non-interactively
        '-r'    : '='       ,   # give run name
        '-n'    : ''        ,   # do not actually execute any processes
        } )

    #
    #

    all = opt['-a']
    no_run = opt['-n']

    di_nodes = nodes.read_file_list( args )

    xnodes = di_nodes.node_index

    if '-r' in opt :
        run_name = opt['-r']
    else :
        run_name = "user_%s_%s"%(username,str(datetime.datetime.now()).replace(' ','_'))

    db = steuermann.config.open_db()

    if all :
        run_all(xnodes, run_name, db)
    else :
        run_interactive( xnodes, run_name, db )

#

def find_wild_names( xnodes, name ) :
    print "find_wild",name
    l = [ ]
    for x in xnodes :
        if nodes.wildcard_name( name, x ) :
            print "...",x
            l.append(x)
    return l
#

def do_flag( xnodes, name, recursive, fn, verbose ) :
    if verbose :
        verbose = verbose + 1
    if not (':' in name ) and not ('/' in name) :
        name = '*:*/'+name
    if not ':' in name :
        name = '*:' + name
    if ( '*' in name )  or ( '?' in name ) or ( '[' in name ) :
        if verbose :
            print '  '*verbose, "wild",name
        for x in xnodes :
            if nodes.wildcard_name( name, x ) :
                if verbose :
                    print '  '*verbose, "match",x
                do_flag( xnodes, x, recursive, fn, verbose )
    elif name in xnodes :
        if verbose :
            print '  '*verbose, "found",name
        fn(xnodes[name])
        if recursive :
            for y in xnodes[name].predecessors : 
                do_flag( xnodes, y.name, recursive, fn, verbose )
    else :
            if verbose :
                print '  '*verbose, "not in list", name

def set_want( node ) :
    # if we said we want it, mark it as wanted and don't skip
    node.wanted = 1
    node.skip = 0

def set_skip( node ) :
    # If we want to skip it, mark it as IS wanted and skip.
    # Wanted makes us try to run it, then skip makes the run a nop.
    # This means that stuff that comes after it can run, but only
    # at the right point in the sequence.
    node.wanted = 1
    node.skip = 1


def cmd_flagging( l, xnodes, func ) :
    if l[1] == '-r' :
        recursive = 1
        l = l[2:]
    else :
        recursive = 0
        l = l[1:]
    
    for x in l :
        do_flag( xnodes, x, recursive, func, 1 )


#
def print_node(xnodes, x, print_recursive, print_all, indent=0):
    print ' '*indent, xnodes[x].wanted, xnodes[x].finished, xnodes[x].skip,  x
    if print_all :
        l = [ a.name for a in xnodes[x].predecessors ]
        print ' '*indent, "       AFTER", '  '.join(l)
        if print_recursive :
            for x in l :
                print_node( xnodes, x, print_recursive, print_all, indent=indent+8)

#

helpstr = """

reset               start a new run
start               run things and wait for them to finish
skip [-r] node      skip this node
want [-r] node      declare that we want this node

wr                  want/skip report
dr                  depth report
conditions (cond)   list all conditions
hostgroups (hg)     list all host groups
list -a
list node

wait                like start

pre [ nodenames ]   show predecessors to nodes
pre node            show what must come before a node
report              show report 

"""

def run_interactive( xnodes, run_name, db) :

    org_run_name = run_name
    run_count = 0

    register_database(db, run_name, xnodes)

    runner = run.runner( xnodes )

    for x in xnodes :
        xnodes[x].finished = 0
        xnodes[x].running  = 0
        xnodes[x].wanted   = 0
        xnodes[x].skip     = 1

    print "Defaulting all to SKIP"

    keep_running = 0

    while 1 :
        try :
            l = raw_input("smc>")
        except EOFError :
            break

        l = l.strip()
        l = l.split()
        if len(l) > 0 :
            n = l[0]
        else :
            n = ''

        if n == '?' :
            print helpstr

        elif n == 'd' :
            run.debug=0
            if len(l) > 1 :
                for x in l[1:] :
                    print "XXXXXXXXXX"
                    print "SECTION",x
                    print runner.get_host_info(x)
                    print ""
            else :
                for x in runner.cfg.sections() :
                    print "XXXXXXXXXX"
                    print "SECTION",x
                    print runner.get_host_info(x)
                    print ""
            run.debug=0

        elif n == 'report' :
            print report.report_text( db, run_name )

        elif n == 'hostgroups' or n == 'hostgroup' or n == 'hg' :
            print_hostgroups()

        elif n == 'conditions' or n == 'condition' or n == 'cond':
            print_conditions()

        elif n == 'wr' :
            print report.report_text( db, run_name, info_callback_want )

        elif n == 'dr' :
            print report.report_text( db, run_name, info_callback_depth )

        elif n == 'pre' :
            pre_cmd( l[1:], xnodes )

        elif n == 'want' :
            cmd_flagging( l, xnodes, set_want )

        elif n == 'skip' :
            cmd_flagging( l, xnodes, set_skip )

        elif n == 'reset' :
            print "marking all as not finished"
            for x in xnodes :
                xnodes[x].finished = 0
            
            run_name = org_run_name + '.%d'%run_count
            run_count = run_count + 1
            print "new run name",run_name
            register_database(db, run_name, xnodes)

        elif n == 'list' :
            l = l[1:]
            if len(l) > 0 and l[0] == '-a' :
                l = l[1:]
                print_all = 1
            else :
                print_all = 0

            if len(l) > 0 and l[0] == '-r' :
                l = l[1:]
                print_recursive=1
            else :
                print_recursive=0

            if len(l) == 0 :
                all = [ x for x in xnodes ]
            else :
                all = [ ]
                for x in l :
                    all = all + find_wild_names( xnodes, x )

            all = sorted(all)
            print "recursive",print_recursive
            print "w f s name"
            for x in all :
                print_node(xnodes, x, print_recursive, all)

        elif n == 'wait' or n == 'start' :
            c = db.cursor()
            for x in xnodes :
                host, tablename, cmd = nodes.crack_name(x)
                if xnodes[x].wanted :
                    status = 'W'
                    c.execute("UPDATE sm_status SET status = 'W' WHERE run = ? AND host = ? AND tablename = ? AND cmd = ? AND status = 'N'",
                        (run_name, host, tablename, cmd) )

            db.commit()

            while 1 :
                ( keep_running, no_sleep ) = run_step( runner, xnodes, run_name, db )
                if not keep_running :
                    break
                if not no_sleep :
                    time.sleep(1)
                if keypress() :
                    print "wait interrupted (processes continue)"
                    break

        else :
            print "unrecognized"

        if keep_running :
            print "run step"
            ( keep_running, no_sleep ) = run_step( runner, xnodes, run_name, db )

            if len(runner.all_procs) == 0 :
                # give it a chance to start another
                ( keep_running, no_sleep ) = run_step( runner, xnodes, run_name, db )

            if not keep_running :
                    print 'all done'

            else :
                if len(runner.all_procs) == 0 :
                    print "no processes running - some prereq not satisfiable"
        

#

def match_all_nodes( l, xnodes ) :

    # all will be the list of all nodes that we want to process
    all = [ ]

    # for all the names they said on the command line
    for x in l :

        # use wild cards for unspecified prefix parts.  i.e. "arf" means "*:*/arf"
        x = nodes.normalize_name('*','*',x)

        # find all the nodes that match the pattern
        for y in xnodes :
            if nodes.wildcard_name( x, y ) :
                all.append(y)

    return sorted(all)

#

def pre_cmd( l, xnodes ) :

    for x in match_all_nodes( l, xnodes ) :
        print "-----"
        print x
        print_pre(x, xnodes, 1)
            

def print_pre(who, xnodes, depth) :
    pre = xnodes[who].predecessors 
    for x in pre :
        x = x.name
        print '  '*depth+ x
        print_pre( x, xnodes, depth+1)

#

def register_database(db, run, xnodes ) :
    c = db.cursor()
    c.execute('INSERT INTO sm_runs ( run, create_time ) VALUES ( ?, ? )', ( run, str(datetime.datetime.now()).replace(' ','_')) )
    
    c = db.cursor()
    for x in xnodes :
        host, tablename, cmd = nodes.crack_name(x)
        depth = xnodes[x].depth
        c.execute("INSERT INTO sm_status ( run, host, tablename, cmd, depth, status ) VALUES "
            "( ?, ?, ?, ?, ?, 'N' )", ( run, host, tablename, cmd, depth ) )

    db.commit()

#

def run_all(xnodes, run_name, db) :

    for x in xnodes :
        x = xnodes[x]
        x.finished = 0
        x.running  = 0
        x.wanted   = 1
        x.skip     = 0

    register_database(db, run_name, xnodes)

    runner = run.runner( xnodes )

    none_running = 0    
        # will count how many times through there was nothing running

    while 1 :
        ( keep_running, no_sleep ) = run_step( runner, xnodes, run_name, db )
        if not keep_running :
            break
        if not no_sleep :
            if len(runner.all_procs) == 0 :
                none_running += 1
                if none_running > 5 :
                    print "No processes running - some prereq missing"
                    break
            else :
                none_running = 0
            time.sleep(1)

#

def run_step( runner, xnodes, run_name, db ) :
    
        # flag to keep running 
        keep_running = 0

        # flag to suppress brief sleep at end of loop
        no_sleep = 0

        # Loop, polling for work to do, or for finishing processes
        for x_name in xnodes :
            x=xnodes[x_name]

            # skip nodes that we do not need to consider running because

            # - it is not wanted
            if not x.wanted :
                continue

            # - it is already finished
            if x.finished :
                continue

            # - we are already running it
            if x.running :
                keep_running=1
                continue

            # ok, if we are here, we found a node that we want to run

            # if there is a node we need to run, we need to come back through the loop
            # (bug: are we sure there is not a deadlock caused by mutual dependencies? if that happens, it can never run.)
            keep_running = 1
            
            # count how many of the predecessors are finished
            released = sum( [ xnodes[r].finished for r in x.released ])

            # if the number of predecessors finished is the number
            # of predecessors, we can run this one
            if released == len(x.released) :
                host, table, cmd = nodes.crack_name(x_name)

                # we are now ready to let it run.  If it is marked skipped, just say it ran really fast.
                if x.skip :
                    x.finished = 1
                    no_sleep = 1
                    keep_running = 1
                    db.execute("UPDATE sm_status SET start_time = ?, status = 'S' WHERE ( run = ? AND host = ? AND tablename = ? AND cmd = ? )",
                            ( str(datetime.datetime.now()), run_name, host, table, cmd ) )
                    db.commit()

                else :
                    try :
                        tmp = runner.run(x, run_name, no_run=no_run, logfile_name = make_log_file_name(run_name, host, table, cmd) ) 
                        # print "STARTED",x_name
                    except run.run_exception, e :
                        now = str(datetime.datetime.now())
                        db.execute("UPDATE sm_status SET start_time=?, end_time=?, status='E', notes=? WHERE ( run=? AND host=? AND tablename=? AND cmd=? )",
                                ( now, now, repr(e), run_name, host, table, cmd ) )
                        x.finished = 1
                        no_sleep = 1
                        keep_running = 1
                    else :
                        if tmp == 'R' :
                            db.execute("UPDATE sm_status SET start_time = ?, status = 'R' WHERE ( run = ? AND host = ? AND tablename = ? AND cmd = ? )",
                                ( str(datetime.datetime.now()), run_name, host, table, cmd ) )
                        elif tmp == 'D' :
                            # same as skip above
                            x.finished = 1
                            no_sleep = 1
                            keep_running = 1
                            db.execute("UPDATE sm_status SET start_time = ?, status = 'S' WHERE ( run = ? AND host = ? AND tablename = ? AND cmd = ? )",
                                    ( str(datetime.datetime.now()), run_name, host, table, cmd ) )
                        elif tmp == 'M' :
                            # hit max proc - not run, but try again later
                            pass
                        else :
                            print "WARNING: runner.run() returned unknown code %s"%str(tmp)

                    db.commit()
                        

        # if anything has exited, we process it and update the status in the database
        while 1 :
            who_exited = runner.poll() 
            if not who_exited :
                break

            print "SOMETHING EXITED",who_exited
            # yes, something exited - no sleep, and keep running
            no_sleep = 1
            keep_running = 1

            # note who and log it
            x_host, x_table, x_cmd = nodes.crack_name(who_exited[0])

            db.execute("UPDATE sm_status SET end_time = ?, status = ?  WHERE ( run = ? AND host = ? AND tablename = ? AND cmd = ? )",
                    ( str(datetime.datetime.now()), who_exited[1], run_name, x_host, x_table, x_cmd ) )
            db.commit()

        # runner.display_procs()

        return ( keep_running, no_sleep )

#####

ms_windows = 0

if ms_windows :
    import msvcrt
else :
    import select

def keypress() :
    if ms_windows :
        return msvcrt.kbhit()
    else :
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

#####

def info_callback_want( db, run, tablename, host, cmd ) :
    n = xnodes['%s:%s/%s'%(host,tablename,cmd)]
    s = ''
    if n.skip :
        s = s + 'S'
    if n.wanted :
        s = s + 'W'
    if s == '' :
        s = '-'
    return s

def info_callback_depth( db, run, tablename, host, cmd ) :
    n = xnodes['%s:%s/%s'%(host,tablename,cmd)]
    return n.depth

#####
def make_log_file_name( run_name, table, host, cmd ) :
        return '%s/run/%s/%s/%s/%s.log'%(steuermann.config.logdir, run_name, table, host, cmd)


if __name__ == '__main__' :
    main()

#####
def print_hostgroups() :
    print ""
    l = sorted( [ x for x in nodes.hostgroups ] )
    for x in l :
        print "%s:"%x
        l1 = sorted( [ y for y in nodes.hostgroups[x] ] )
        for y in l1 :
            print "    %s"%y
        print ""

#####
def print_conditions() :
    boring = { }
    exec 'pass' in boring
    l = sorted( [ x for x in nodes.saved_conditions ] )
    row = 0

    tt = text_table.text_table()
    
    for x in l :
        if x in boring :
            continue
        if callable(x) :
            v = x()
        else :  
            v = nodes.saved_conditions[x]
        tt.set_value(row,0,x)
        tt.set_value(row,1,str(v))
        row = row + 1

    print tt.get_rst()
