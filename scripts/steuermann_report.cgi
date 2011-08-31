#! python

import cgi
import cgitb
import os
import sys
import re
import datetime


STEUERMANN_DIR_HERE
sys.path.insert(0, addpath)

import steuermann.config

cgitb.enable()

form = cgi.FieldStorage(keep_blank_values=1)
cginame = os.getenv("SCRIPT_NAME")

def sqltime(arg) :
    if arg is None :
        return None

    if '.' in arg :
        x = arg.split('.')
        d = datetime.datetime.strptime(x[0],'%Y-%m-%d %H:%M:%S')
        d = d.replace(microsecond=int((x[1]+'000000')[0:6]))
    else :
        x = time.strptime(arg,'%Y-%m-%d %H:%M:%S')
        d = datetime.datetime(year=x[0], month=x[1], day=x[2],
        hour=x[3], minute=x[4], second=x[5] )
        # not in 2.4:
        # d = datetime.datetime.strptime(arg,'%Y-%m-%d %H:%M:%S')
    return d


if not 'action' in form :
    print 'content-type: text/html'
    print ''
    db = steuermann.config.open_db()
    c = db.cursor()
    c.execute('SELECT DISTINCT run FROM status ORDER BY run DESC')
    for run, in c :
        print "<a href=%s?action=status&run=%s>%s</a><br>"%(cginame, run, run)
    sys.exit(0)

action = form['action'].value

if action == 'status' :
    db = steuermann.config.open_db()
    import steuermann.report
    steuermann.report.cginame = cginame
    print 'content-type: text/html'
    print ''
    run = form['run'].value
    print steuermann.report.report_html( db, run, info_callback=steuermann.report.info_callback_gui )
    sys.exit(0)

elif action == 'log' :
    print 'content-type: text/plain'
    print ''

    # crack apart the parameter run/host:table/cmd
    name = re.match('(.*)/(.*):(.*)/(.*)', form['name'].value)
    run = name.group(1)
    host = name.group(2)
    table = name.group(3)
    cmd = name.group(4)


    db = steuermann.config.open_db()
    c = db.cursor()
    c.execute("SELECT status, start_time, end_time, notes FROM status WHERE run = ? AND host = ? AND tablename = ? AND cmd = ?",(
            run, host, table, cmd ) )
    x = c.fetchone()
    if x is None :
        print "No such record in database",run,host,table,cmd
        sys.exit(0)

    status, start_time, end_time, notes = x

    print "%s %s:%s/%s"%(run, host, table, cmd)
    print "status: %s"%status
    print ""
    print "start: %s"%start_time
    print "end  : %s"%end_time
    start_time = sqltime(start_time)
    end_time = sqltime(end_time)
    if isinstance(end_time,datetime.datetime) and isinstance(end_time,datetime.datetime) :
        print "dur  : %s"%(end_time-start_time)

    if not notes is None :
        print "notes:"
        for x in [ '    ' + x for x in notes.split('\n') ] :
            print x
    print ""
    print "--------------------"
    filename = '%s/%s/%s:%s.%s.log'%(steuermann.config.logdir,run,host,table,cmd)
    f=open(filename,'r')
    while 1 :
        x = f.read(65536)
        if x == '' :
            break
        sys.stdout.write(x)
    sys.exit(0)

print 'content-type: text/html'
print ''
print 'no action?'

