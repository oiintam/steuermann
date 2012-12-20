# THIS FILE WAS AUTOMATICALLY GENERATED

# Parse a Steuermann Spec file
#
# This is an exyapps grammer in specfile.exy
import nodes


# Begin -- grammar generated by Yapps
import sys, re
###### included from /Users/cslocum/sm/build/urwd/python/lib/python/exyapps/runtime.py
# exyapps - yet another python parser system
# Copyright 1999-2003 by Amit J. Patel <amitp@cs.stanford.edu>
# Enhancements copyright 2003-2004 by Matthias Urlichs <smurf@debian.org>
# Copyright 2011 by Association of Universities for Research in Astronomy
#
# This software can be distributed under the terms of the MIT
# open source license, either found in the LICENSE file or at
# <http://www.opensource.org/licenses/mit-license.php>
#
# -----
#
# Changes from the debian version:
# - indented with spaces, not tabs
# - when you instantiate the parser object, you can pass in an object
#   data=XXX that will be available to the parser as self.data; this
#   is basically a hook to provide parser-global data.
#
# Note that this file is incorporated directly into the generated parser.
# Take care when defining new file-global names because the generated
# parser has its own globals.

"""Run time libraries needed to run parsers generated by Yapps.

This module defines parse-time exception classes, a scanner class, a
base class for parsers produced by Yapps, and a context class that
keeps track of the parse stack.

"""

import sys, re

MIN_WINDOW=4096
# File lookup window

class SyntaxError(Exception):
    """When we run into an unexpected token, this is the exception to use"""
    def __init__(self, pos=None, msg="Bad Token", context=None):
        Exception.__init__(self)
        self.pos = pos
        self.msg = msg
        self.context = context

    def __str__(self):
        if not self.pos: return 'SyntaxError'
        else: return 'SyntaxError@%s(%s)' % (repr(self.pos), self.msg)

class NoMoreTokens(Exception):
    """Another exception object, for when we run out of tokens"""
    pass

class Token(object):
    """Yapps token.

    This is a container for a scanned token.
    """

    def __init__(self, type,value, pos=None):
        """Initialize a token."""
        self.type = type
        self.value = value
        self.pos = pos

    def __repr__(self):
        output = '<%s: %s' % (self.type, repr(self.value))
        if self.pos:
            output += " @ "
            if self.pos[0]:
                output += "%s:" % self.pos[0]
            if self.pos[1]:
                output += "%d" % self.pos[1]
            if self.pos[2] is not None:
                output += ".%d" % self.pos[2]
        output += ">"
        return output

in_name=0
class Scanner(object):
    """Yapps scanner.  (lexical analyzer)

    The Yapps scanner can work in context sensitive or context
    insensitive modes.  The token(i) method is used to retrieve the
    i-th token.  It takes a restrict set that limits the set of tokens
    it is allowed to return.  In context sensitive mode, this restrict
    set guides the scanner.  In context insensitive mode, there is no
    restriction (the set is always the full set of tokens).

    """

    def __init__(self, patterns, ignore, input="",
            file=None,filename=None,stacked=False):
        """Initialize the scanner.

        Parameters:
          patterns : [(terminal, uncompiled regex), ...] or None
          ignore : {terminal:None, ...}
          input : string

        If patterns is None, we assume that the subclass has
        defined self.patterns : [(terminal, compiled regex), ...].
        Note that the patterns parameter expects uncompiled regexes,
        whereas the self.patterns field expects compiled regexes.

        The 'ignore' value is either None or a callable, which is called
        with the scanner and the to-be-ignored match object; this can
        be used for include file or comment handling.
        """

        if not filename:
            global in_name
            filename="<f.%d>" % in_name
            in_name += 1

        self.input = input
        self.ignore = ignore
        self.file = file
        self.filename = filename
        self.pos = 0
        self.del_pos = 0 # skipped
        self.line = 1
        self.del_line = 0 # skipped
        self.col = 0
        self.tokens = []
        self.stack = None
        self.stacked = stacked

        self.last_read_token = None
        self.last_token = None
        self.last_types = None

        if patterns is not None:
            # Compile the regex strings into regex objects
            self.patterns = []
            for terminal, regex in patterns:
                self.patterns.append( (terminal, re.compile(regex)) )

    def stack_input(self, input="", file=None, filename=None):
        """Temporarily parse from a second file."""

        # Already reading from somewhere else: Go on top of that, please.
        if self.stack:
            # autogenerate a recursion-level-identifying filename
            if not filename:
                filename = 1
            else:
                try:
                    filename += 1
                except TypeError:
                    pass
                # now pass off to the include file
            self.stack.stack_input(input,file,filename)
        else:

            try:
                filename += 0
            except TypeError:
                pass
            else:
                filename = "<str_%d>" % filename

#           self.stack = object.__new__(self.__class__)
#           Scanner.__init__(self.stack,self.patterns,self.ignore,input,file,filename, stacked=True)

            # Note that the pattern+ignore are added by the generated
            # scanner code
            self.stack = self.__class__(input,file,filename, stacked=True)

    def get_pos(self):
        """Return a file/line/char tuple."""
        if self.stack: return self.stack.get_pos()

        return (self.filename, self.line+self.del_line, self.col)

#   def __repr__(self):
#       """Print the last few tokens that have been scanned in"""
#       output = ''
#       for t in self.tokens:
#           output += '%s\n' % (repr(t),)
#       return output

    def print_line_with_pointer(self, pos, length=0, out=sys.stderr):
        """Print the line of 'text' that includes position 'p',
        along with a second line with a single caret (^) at position p"""

        file,line,p = pos
        if file != self.filename:
            if self.stack: return self.stack.print_line_with_pointer(pos,length=length,out=out)
            print >>out, "(%s: not in input buffer)" % file
            return

        text = self.input
        p += length-1 # starts at pos 1

        origline=line
        line -= self.del_line
        spos=0
        if line > 0:
            while 1:
                line = line - 1
                try:
                    cr = text.index("\n",spos)
                except ValueError:
                    if line:
                        text = ""
                    break
                if line == 0:
                    text = text[spos:cr]
                    break
                spos = cr+1
        else:
            print >>out, "(%s:%d not in input buffer)" % (file,origline)
            return

        # Now try printing part of the line
        text = text[max(p-80, 0):p+80]
        p = p - max(p-80, 0)

        # Strip to the left
        i = text[:p].rfind('\n')
        j = text[:p].rfind('\r')
        if i < 0 or (0 <= j < i): i = j
        if 0 <= i < p:
            p = p - i - 1
            text = text[i+1:]

        # Strip to the right
        i = text.find('\n', p)
        j = text.find('\r', p)
        if i < 0 or (0 <= j < i): i = j
        if i >= 0:
            text = text[:i]

        # Now shorten the text
        while len(text) > 70 and p > 60:
            # Cut off 10 chars
            text = "..." + text[10:]
            p = p - 7

        # Now print the string, along with an indicator
        print >>out, '> ',text
        print >>out, '> ',' '*p + '^'

    def grab_input(self):
        """Get more input if possible."""
        if not self.file: return
        if len(self.input) - self.pos >= MIN_WINDOW: return

        data = self.file.read(MIN_WINDOW)
        if data is None or data == "":
            self.file = None

        # Drop bytes from the start, if necessary.
        if self.pos > 2*MIN_WINDOW:
            self.del_pos += MIN_WINDOW
            self.del_line += self.input[:MIN_WINDOW].count("\n")
            self.pos -= MIN_WINDOW
            self.input = self.input[MIN_WINDOW:] + data
        else:
            self.input = self.input + data

    def getchar(self):
        """Return the next character."""
        self.grab_input()

        c = self.input[self.pos]
        self.pos += 1
        return c

    def token(self, restrict, context=None):
        """Scan for another token."""

        while 1:
            if self.stack:
                try:
                    return self.stack.token(restrict, context)
                except StopIteration:
                    self.stack = None

        # Keep looking for a token, ignoring any in self.ignore
            self.grab_input()

            # special handling for end-of-file
            if self.stacked and self.pos==len(self.input):
                raise StopIteration

            # Search the patterns for the longest match, with earlier
            # tokens in the list having preference
            best_match = -1
            best_pat = '(error)'
            best_m = None
            for p, regexp in self.patterns:
                # First check to see if we're ignoring this token
                if restrict and p not in restrict and p not in self.ignore:
                    continue
                m = regexp.match(self.input, self.pos)
                if m and m.end()-m.start() > best_match:
                    # We got a match that's better than the previous one
                    best_pat = p
                    best_match = m.end()-m.start()
                    best_m = m

            # If we didn't find anything, raise an error
            if best_pat == '(error)' and best_match < 0:
                msg = 'Bad Token'
                if restrict:
                    msg = 'Trying to find one of '+', '.join(restrict)
                raise SyntaxError(self.get_pos(), msg, context=context)

            ignore = best_pat in self.ignore
            value = self.input[self.pos:self.pos+best_match]
            if not ignore:
                tok=Token(type=best_pat, value=value, pos=self.get_pos())

            self.pos += best_match

            npos = value.rfind("\n")
            if npos > -1:
                self.col = best_match-npos
                self.line += value.count("\n")
            else:
                self.col += best_match

            # If we found something that isn't to be ignored, return it
            if not ignore:
                if len(self.tokens) >= 10:
                    del self.tokens[0]
                self.tokens.append(tok)
                self.last_read_token = tok
                # print repr(tok)
                return tok
            else:
                ignore = self.ignore[best_pat]
                if ignore:
                    ignore(self, best_m)

    def peek(self, *types, **kw):
        """Returns the token type for lookahead; if there are any args
        then the list of args is the set of token types to allow"""
        context = kw.get("context",None)
        if self.last_token is None:
            self.last_types = types
            self.last_token = self.token(types,context)
        elif self.last_types:
            for t in types:
                if t not in self.last_types:
                    raise NotImplementedError("Unimplemented: restriction set changed")
        return self.last_token.type

    def scan(self, type, **kw):
        """Returns the matched text, and moves to the next token"""
        context = kw.get("context",None)

        if self.last_token is None:
            tok = self.token([type],context)
        else:
            if self.last_types and type not in self.last_types:
                raise NotImplementedError("Unimplemented: restriction set changed")

            tok = self.last_token
            self.last_token = None
        if tok.type != type:
            if not self.last_types: self.last_types=[]
            raise SyntaxError(tok.pos, 'Trying to find '+type+': '+ ', '.join(self.last_types)+", got "+tok.type, context=context)
        return tok.value

class Parser(object):
    """Base class for Yapps-generated parsers.

    """

    def __init__(self, scanner, data=None):
        self._scanner = scanner
        self.data = data

    def _stack(self, input="",file=None,filename=None):
        """Temporarily read from someplace else"""
        self._scanner.stack_input(input,file,filename)
        self._tok = None

    def _peek(self, *types, **kw):
        """Returns the token type for lookahead; if there are any args
        then the list of args is the set of token types to allow"""
        return self._scanner.peek(*types, **kw)

    def _scan(self, type, **kw):
        """Returns the matched text, and moves to the next token"""
        return self._scanner.scan(type, **kw)

class Context(object):
    """Class to represent the parser's call stack.

    Every rule creates a Context that links to its parent rule.  The
    contexts can be used for debugging.

    """

    def __init__(self, parent, scanner, rule, args=()):
        """Create a new context.

        Args:
        parent: Context object or None
        scanner: Scanner object
        rule: string (name of the rule)
        args: tuple listing parameters to the rule

        """
        self.parent = parent
        self.scanner = scanner
        self.rule = rule
        self.args = args
        while scanner.stack: scanner = scanner.stack
        self.token = scanner.last_read_token

    def __str__(self):
        output = ''
        if self.parent: output = str(self.parent) + ' > '
        output += self.rule
        return output

def print_error(err, scanner, max_ctx=None):
    """Print error messages, the parser stack, and the input text -- for human-readable error messages."""
    # NOTE: this function assumes 80 columns :-(
    # Figure out the line number
    pos = err.pos
    if not pos:
        pos = scanner.get_pos()

    file_name, line_number, column_number = pos
    print >>sys.stderr, '%s:%d:%d: %s' % (file_name, line_number, column_number, err.msg)

    scanner.print_line_with_pointer(pos)

    context = err.context
    token = None
    while context:
        print >>sys.stderr, 'while parsing %s%s:' % (context.rule, tuple(context.args))
        if context.token:
            token = context.token
        if token:
            scanner.print_line_with_pointer(token.pos, length=len(token.value))
        context = context.parent
        if max_ctx:
            max_ctx = max_ctx-1
            if not max_ctx:
                break

def wrap_error_reporter(parser, rule, *args,**kw):
    try:
        return getattr(parser, rule)(*args,**kw)
    except SyntaxError, e:
        print_error(e, parser._scanner)
    except NoMoreTokens:
        print >>sys.stderr, 'Could not complete parsing; stopped around here:'
        print >>sys.stderr, parser._scanner
###### end of runtime.py

class specfileScanner(Scanner):
    patterns = [
        ('"="', re.compile('=')),
        ('"$"', re.compile('$')),
        ('[ \r\t\n]+', re.compile('[ \r\t\n]+')),
        ('#.*\n', re.compile('#.*\n')),
        ('END', re.compile('$')),
        ('HOSTGROUP', re.compile('HOSTGROUP')),
        ('IF', re.compile('IF')),
        ('IFNOT', re.compile('IFNOT')),
        ('TABLE', re.compile('TABLE')),
        ('HOST', re.compile('HOST')),
        ('CMD', re.compile('CMD')),
        ('OPT', re.compile('OPT')),
        ('AFTER', re.compile('AFTER')),
        ('RUN', re.compile('RUN')),
        ('LOCAL', re.compile('LOCAL')),
        ('IMPORT', re.compile('IMPORT')),
        ('RESOURCE', re.compile('RESOURCE')),
        ('DEBUG', re.compile('DEBUG')),
        ('name', re.compile('[a-zA-Z0-9_.-]+')),
        ('STAR', re.compile('\\*')),
        ('cmdname', re.compile('[a-zA-Z0-9_.-]+')),
        ('tablename', re.compile('[a-zA-Z0-9_.-]+')),
        ('wildname', re.compile('[@]{0,1}[*?a-zA-Z0-9_.-]+')),
        ('string', re.compile('"[^"]*"')),
        ('SLASH', re.compile('/')),
        ('COLON', re.compile(':')),
        ('hostgroup', re.compile('@[a-zA-Z0-9_.-]+')),
        ('number', re.compile('[0-9]+')),
        ('RES_ALL', re.compile('all')),
        ('RES_AVAILABLE', re.compile('available')),
        ('CONDITIONS', re.compile('CONDITIONS[^"]*\n[\\s]*END[ \t]*\n')),
    ]
    def __init__(self, str,*args,**kw):
        Scanner.__init__(self,None,{'[ \r\t\n]+':None,'#.*\n':None,},str,*args,**kw)

class specfile(Parser):
    Context = Context
    def start(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'start', [])
        table_list = self.table_list(_context)
        self._scan('"$"', context=_context)
        return table_list

    def table_list(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'table_list', [])
        while 1:
            table_section = self.table_section(_context)
            if self._peek('DEBUG', 'CONDITIONS', 'TABLE', 'IMPORT', 'HOSTGROUP', '"$"', 'IF', 'IFNOT', 'COLON', 'name', 'hostgroup', 'CMD', context=_context) not in ['DEBUG', 'CONDITIONS', 'TABLE', 'IMPORT', 'HOSTGROUP']: break

    def table_section(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'table_section', [])
        _token = self._peek('DEBUG', 'CONDITIONS', 'TABLE', 'IMPORT', 'HOSTGROUP', context=_context)
        if _token == 'DEBUG':
            DEBUG = self._scan('DEBUG', context=_context)
            string = self._scan('string', context=_context)
            print "-->debug: %s"%string
        elif _token == 'HOSTGROUP':
            hostgroup_def = self.hostgroup_def(_context)
        elif _token == 'CONDITIONS':
            CONDITIONS = self._scan('CONDITIONS', context=_context)
            nodes.declare_conditions( CONDITIONS, self._scanner.filename )
        elif _token == 'TABLE':
            TABLE = self._scan('TABLE', context=_context)
            tablename = self._scan('tablename', context=_context)
            table_name = tablename
            HOST = self._scan('HOST', context=_context)
            hostlist = [ ]
            while 1:
                _token = self._peek('name', 'hostgroup', context=_context)
                if _token == 'name':
                    name = self._scan('name', context=_context)
                    hostlist.append(name)
                else: # == 'hostgroup'
                    hostgroup = self._scan('hostgroup', context=_context)
                    hostlist = hostlist + nodes.get_hostgroup( hostgroup )
                if self._peek('name', 'hostgroup', 'IF', 'IFNOT', 'CMD', context=_context) not in ['name', 'hostgroup']: break
            while 1:
                cond_command = self.cond_command(tablename,hostlist, _context)
                if self._peek('IF', 'IFNOT', 'CMD', '"$"', 'DEBUG', 'CONDITIONS', 'TABLE', 'IMPORT', 'HOSTGROUP', 'COLON', 'name', 'hostgroup', context=_context) not in ['IF', 'IFNOT', 'CMD']: break
        else: # == 'IMPORT'
            IMPORT = self._scan('IMPORT', context=_context)
            string = self._scan('string', context=_context)
            self.data.import_list.append( string[1:-1] )

    def hostgroup_def(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'hostgroup_def', [])
        HOSTGROUP = self._scan('HOSTGROUP', context=_context)
        hostgroup = self._scan('hostgroup', context=_context)
        nodes.define_hostgroup( hostgroup)
        while 1:
            hostgroup_front = self.hostgroup_front(hostgroup, _context)
            hostgroup_back = self.hostgroup_back(hostgroup,hostgroup_front, _context)
            if self._peek('IF', 'IFNOT', 'COLON', 'name', 'hostgroup', '"$"', 'DEBUG', 'CONDITIONS', 'TABLE', 'IMPORT', 'HOSTGROUP', 'CMD', context=_context) not in ['IF', 'IFNOT', 'COLON']: break

    def hostgroup_front(self, hg, _parent=None):
        _context = self.Context(_parent, self._scanner, 'hostgroup_front', [hg])
        _token = self._peek('IF', 'IFNOT', 'COLON', context=_context)
        if _token == 'IF':
            IF = self._scan('IF', context=_context)
            name = self._scan('name', context=_context)
            return     nodes.check_condition(name, self._scanner.filename )
        elif _token == 'IFNOT':
            IFNOT = self._scan('IFNOT', context=_context)
            name = self._scan('name', context=_context)
            return not nodes.check_condition(name, self._scanner.filename )
        else: # == 'COLON'
            return True

    def hostgroup_back(self, hg,accept_nodes, _parent=None):
        _context = self.Context(_parent, self._scanner, 'hostgroup_back', [hg,accept_nodes])
        COLON = self._scan('COLON', context=_context)
        while self._peek('name', 'hostgroup', 'IF', 'IFNOT', 'COLON', '"$"', 'DEBUG', 'CONDITIONS', 'TABLE', 'IMPORT', 'HOSTGROUP', 'CMD', context=_context) in ['name', 'hostgroup']:
            _token = self._peek('name', 'hostgroup', context=_context)
            if _token == 'name':
                name = self._scan('name', context=_context)
                if accept_nodes : nodes.add_hostgroup( hg, name )
            else: # == 'hostgroup'
                hostgroup = self._scan('hostgroup', context=_context)
                if accept_nodes : nodes.add_hostgroup( hg, hostgroup )

    def cond_command(self, table_name,hostlist, _parent=None):
        _context = self.Context(_parent, self._scanner, 'cond_command', [table_name,hostlist])
        _token = self._peek('IF', 'IFNOT', 'CMD', context=_context)
        if _token == 'IF':
            IF = self._scan('IF', context=_context)
            name = self._scan('name', context=_context)
            COLON = self._scan('COLON', context=_context)
            command = self.command(_context)
            if nodes.check_condition(name, self._scanner.filename ) : self.data.add_command_list( table_name, hostlist, [ command ] )
        elif _token == 'IFNOT':
            IFNOT = self._scan('IFNOT', context=_context)
            name = self._scan('name', context=_context)
            COLON = self._scan('COLON', context=_context)
            command = self.command(_context)
            if not nodes.check_condition(name, self._scanner.filename ) : self.data.add_command_list( table_name, hostlist, [ command ] )
        else: # == 'CMD'
            command = self.command(_context)
            self.data.add_command_list( table_name, hostlist, [ command ] )

    def command(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'command', [])
        CMD = self._scan('CMD', context=_context)
        cmd_pos = self._scanner.get_pos()
        script_type = 'l'
        resources = { 'cpu' : 1 }
        cmdname = self._scan('cmdname', context=_context)
        cmd_name=cmdname; script=cmdname; x_after_clause = [ ]
        if self._peek('RUN', 'LOCAL', 'RESOURCE', 'AFTER', 'IF', 'IFNOT', 'CMD', '"$"', 'DEBUG', 'CONDITIONS', 'TABLE', 'IMPORT', 'HOSTGROUP', 'COLON', 'name', 'hostgroup', context=_context) in ['RUN', 'LOCAL']:
            _token = self._peek('RUN', 'LOCAL', context=_context)
            if _token == 'RUN':
                RUN = self._scan('RUN', context=_context)
                string = self._scan('string', context=_context)
                script = string[1:-1]; script_type='r'
            else: # == 'LOCAL'
                LOCAL = self._scan('LOCAL', context=_context)
                string = self._scan('string', context=_context)
                script = string[1:-1]; script_type='l'
        while self._peek('RESOURCE', 'AFTER', 'IF', 'IFNOT', 'CMD', '"$"', 'DEBUG', 'CONDITIONS', 'TABLE', 'IMPORT', 'HOSTGROUP', 'COLON', 'name', 'hostgroup', context=_context) in ['RESOURCE', 'AFTER']:
            after_pos = self._scanner.get_pos()
            if self._peek('RESOURCE', 'AFTER', context=_context) == 'RESOURCE':
                RESOURCE = self._scan('RESOURCE', context=_context)
                resource_defs = self.resource_defs(_context)
                resources.update(resource_defs)
            AFTER = self._scan('AFTER', context=_context)
            optword = self.optword(_context)
            after_spec = self.after_spec(_context)
            x_after_clause.append( (after_spec, optword, after_pos) )
        return ( cmd_name, script, script_type, x_after_clause, cmd_pos, resources )

    def resource_defs(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'resource_defs', [])
        rl = { }
        while self._peek('name', 'AFTER', context=_context) == 'name':
            name = self._scan('name', context=_context)
            self._scan('"="', context=_context)
            _token = self._peek('number', 'RES_ALL', 'RES_AVAILABLE', context=_context)
            if _token == 'number':
                number = self._scan('number', context=_context)
                ans = int(number)
            elif _token == 'RES_ALL':
                RES_ALL = self._scan('RES_ALL', context=_context)
                ans = 'all'
            else: # == 'RES_AVAILABLE'
                RES_AVAILABLE = self._scan('RES_AVAILABLE', context=_context)
                ans = 'available'
            rl[name] = ans
        print rl ; return rl

    def optword(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'optword', [])
        _token = self._peek('OPT', 'wildname', context=_context)
        if _token == 'OPT':
            OPT = self._scan('OPT', context=_context)
            return 0
        else: # == 'wildname'
            return 1

    def after_spec(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'after_spec', [])
        wildname = self._scan('wildname', context=_context)
        rval = wildname
        if self._peek('COLON', 'SLASH', 'RESOURCE', 'AFTER', 'IF', 'IFNOT', 'CMD', '"$"', 'DEBUG', 'CONDITIONS', 'TABLE', 'IMPORT', 'HOSTGROUP', 'name', 'hostgroup', context=_context) == 'COLON':
            COLON = self._scan('COLON', context=_context)
            wildname = self._scan('wildname', context=_context)
            rval = rval + ':' + wildname
        if self._peek('SLASH', 'RESOURCE', 'AFTER', 'IF', 'IFNOT', 'CMD', '"$"', 'DEBUG', 'CONDITIONS', 'TABLE', 'IMPORT', 'HOSTGROUP', 'COLON', 'name', 'hostgroup', context=_context) == 'SLASH':
            SLASH = self._scan('SLASH', context=_context)
            wildname = self._scan('wildname', context=_context)
            rval = rval + '/' + wildname
        return rval


def parse(rule, text):
    P = specfile(specfileScanner(text))
    return wrap_error_reporter(P, rule)

# End -- grammar generated by Yapps



