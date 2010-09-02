#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#   make_selenium.py - Selenium test's filter
#
# Copyright (c) 2006  Michal Kwiatkowski <ruby@joker.linuxstuff.pl>
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# * Neither the name of the author nor the names of his contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 

__version__ = '0.9.5'


"""
Make Selenium test files from Python sources.

Not every Python programmer have to know HTML to use Selenium. Although
tests format uses only <table>'s, <tr>'s and <td>'s it still consumes
too much place and is hard to modify and maintain. With this script
you'll be able to write Selenium commands in Python language. Before
running Selenium, execute this script on your .py tests and it will
generate appropriate .html files.

Usage:
    python make_selenium.py source_directory destination_directory

Files in source_directory that doesn't start with '_' will be parsed and
HTML files will be generated from them. They will be saved to
destination_directory along with index.html file which lists all tests
so that Selenium Test Runner could find them.

You can also run make_selenium.py with a file as a argument:

    python make_selenium.py source_file [ destination_file ]

Source file will be parsed and saved to destination file. If second
argument is not present, name of original file will be used, with
extension changed to .html. Not index.html will be created.

Test source files format is minimalistic. Use docstring at the beginning
of test as its description. Selenium commands are defined with S()
function which requires 1-3 arguments. They correspond to the standard
"command", "target" and "value" arguments of Selenium command. If you
want to open an install.py script, simply write:

    S('open', 'install.py')

Compare it to the standard Selenium code:

    <tr>
        <td>open</td>
        <td>install.py</td>
        <td></td>
    </tr>

Commands can also be written in more Pythonic fashion, changing first
argument string to method call:

    S.open('install.py')

List of commands is not closed or binded to specific Selenium version,
so you can use any arbitrary string and you won't be warned. This is
needed for future compatibility.

make_selenium understands both CamelCase and underscore_names notation.
So you can either write "S.clickAndWait" or "S.click_and_wait".

As an addition, lines that contain nothing but a comment will be listed
line by line in a test files, put into an unordered list ( <ul> ).

Of course that's not the end of features. Because now you can use Python
to write tests, why not to use its power? See how easy it is to check
different e-mail addresses in your web application form. No more
copy-and-paste!

    bogus_addresses = [
        'mail.address@withoutdot',
        'mail.address.without.at',
        'very_long.and@bogus.email_address.org',
        'address_with@too.much..dots',
        'address_with@-bogus.host.name',
    ]

    for address in bogus_addresses:
        S.type('mail', address)
        S.clickAndWait('check_mail_address')
        S.assertTextPresent('Bogus address!')

Now you have five automated tests of your e-mail checker. Adding another
is a matter of adding another element to bogus_addresses list.

Some tests require to fill in a lot of input fields, as well as checking
long lists of field's values. This script doesn't support you with a
function that generates more that one command. But remember you have
Python in your hands. Define function F() that wraps 'type' command and
function A() that wraps 'assertValue':

    def F(mapping):
        for key, value in mapping.iteritems():
            S.type(key, value)

    def A(mapping):
        for key, value in mapping.iteritems():
            S.assertValue(key, value)

Both of them take a dictionary of field name -> value pairs. So, when
you need to check if certain fields don't loose their values after a
submit, just write:

    data = {
        'forename': 'John',
        'surname': 'Smith',
        'age': '25',
    }

    F(data)
    S.clickAndWait('submit_data')
    A(data)

Wasn't that nice?

Knowing how easily this system can be extended you would probably end up
creating your own little library of handy functions. To include
definitions from other file use I() function. It takes one argument
which is path to a file you want to include (relative to the
source_directory given on the command line). It works more like C
preprocessor #include directive than Python import, as all symbols
defined go to common namespace.

But that's not all. With make_selenium.py you can combine two powerful
tools: Selenium IDE ( http://www.openqa.org/selenium-ide/ ) and Python.
Selenium IDE can record tests directly from your browser, so it's easy
to create new tests. Its main disadvantage is HTML output, native
format for the Selenium, but hard to maintain and modify. But that's
not a problem for make_selenium. You can convert your old tests from
HTML to Python, using -p option:

    python make_selenium.py -p source_file [ destination_file ]

You can also convert whole bunch of tests:

    python make_selenium.py -p source_directory destination_directory

As you see, migrating to make_selenium.py is very easy and
straightforward.
"""


import os
import re
import stat
import sys
import unittest


index_template_begin = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
    <head>
        <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
        <title>Canoe test page</title>
        <style>
            #content {
                font-family: Verdana,Arial,Helvetica,sans-serif;
                font-size: 12px;

                margin: 1em auto;
                padding: 1em;

                border: 1px solid #696;
                background-color: #cfc;
            }
            h1 {
                font-size: 200%;
                text-align: center;

                margin: 0;
                padding: 0;
            }
            p.info {
                font-style: italic;
            }
            table td:before {
                content: " »";
            }
        </style>
    </head>

    <body>
        <div id="content">

        <table>
            <th>Canoe test suite</th>
"""

index_template_content = """
            <tr><td>
                <a href="%(filename)s">%(title)s</a>
                - %(description)s
            </td></tr>
"""

index_template_end = """
        </table>

        </div>
    </body>
</html>
"""

test_template_begin = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
    <head>
        <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
        <style>
            table {
                width: 100%;
                empty-cells: show;
                border: 1px solid #000;
                border-collapse: collapse;
            }
                table th {
                    font-weight: bold;
                    text-align: center;

                    border: 2px solid #000;
                    padding: 6px;
                }
                table td {
                    font-family: monospace;

                    border: 1px solid #000;
                    padding: 6px;
                }
        </style>
    </head>
    <body>
"""

test_template_mid = """
        <table>
            <tr><th colspan="3">%s</th></tr>
"""

test_template_test = """
            <tr>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
            </tr>
"""

test_template_end = """
        </table>
    </body>
</html>
"""


################################################################################
#  Helper functions
################################################################################

def underscore2camel(name):
    """Convert name from underscore_name to CamelCase.

    >>> underscore2camel('assert_text_present')
    'assertTextPresent'
    >>> underscore2camel('click')
    'click'
    >>> underscore2camel('goBack')
    'goBack'
    """
    def upper(match):
        return match.group(1).upper()
    return re.sub(r'_([a-z])', upper, name)


def change_extension(filename, extension):
    """Change file extenstion to @extension.

    >>> change_extension('file_name.py', 'html')
    'file_name.html'
    >>> change_extension('file_name.with.dots.html', 'py')
    'file_name.with.dots.py'
    """
    return '.'.join(filename.split('.')[:-1] + [extension])


def _stat_checker(fun):
    def new_f(node):
        state = os.lstat(node)
        if fun(state.st_mode):
            return True
        return False

    return new_f


is_file = _stat_checker(stat.S_ISREG)
is_dir = _stat_checker(stat.S_ISDIR)


def read_str_from_file(filename):
    fd = open(filename)
    content = fd.read()
    fd.close()
    return content


def write_str_to_file(string, filename):
    fd = open(filename, 'w')
    fd.write(string)
    fd.close()


def _missing_method(methodname):
    def method(self, *args):
        raise Exception, "Class %s should define %s method." % (self.__class__, methodname)
    return method


################################################################################
#  Converters.
################################################################################

class CodeGenerator(object):
    generate = _missing_method('generate')


class SourceParser(object):
    get_test_from_file = _missing_method('get_test_from_file')

    def get_tests_from_dir(self, dir):
        tests = map(lambda x: self.get_test_from_file(x, dir),
                filter(lambda x: not x.startswith('_') and is_file(os.path.join(dir, x)),
                        os.listdir(dir)))
        tests.sort()

        return tests


class FromHtml(SourceParser):
    def get_test_from_file(self, filename, directory):
        content = read_str_from_file(os.path.join(directory, filename))

        def get_title():
            m = re.search(r'<title>([^<]+)</title>', content)
            if m:
                return m.group(1)
            return ''

        def get_commands():
            comm_regex = r'<t[dh][^>]*>([^<]*)</t[dh]>'
            return re.findall(r'<tr>\s*' + (comm_regex + '\s*') * 3 +  '</tr>', content)

        return Test(filename,
                directory,
                get_title(),
                "No description.",
                '',
                get_commands())


class FromPython(SourceParser):
    def eval_recusively(self, filename, directory):
        """Evaluate file in context that defines Selenium object binded to S.

        All calls to I() as well as file path is relative to @dir.
        """
        alist = []

        class Selenium(object):
            def __S(arg1, arg2='', arg3=''):
                alist.append((arg1, arg2, arg3))
            __S = staticmethod(__S)

            def __getattr__(self, name):
                def fun(arg2='', arg3=''):
                    return self.__S(underscore2camel(name), arg2, arg3)
                return fun

            def __call__(self, *args):
                return self.__S(*args)

        S = Selenium()

        class C(object): pass
        module = C()

        docstring = [ None ]

        def eval_file(filename):
            # Preserve docstring of the first file that defines it.
            if module.__doc__ and not docstring[0]:
                docstring[0] = module.__doc__

            content = read_str_from_file(os.path.join(directory, filename))

            code = compile(content, '/dev/null', 'exec')

            eval(code, module.__dict__)

        module.S = S
        module.I = eval_file

        eval_file(filename)

        return (alist, docstring[0] or 'No description.')

    def get_test_from_file(self, filename, directory):
        def get_title_from_testname(name):
            name = ''.join(name.split('.')[:-1])
            words = name.split('_')

            if words[0].isdigit():
                words = words[1:]

            words[0] = words[0].capitalize()
            return ' '.join(words)

        def get_comments_from_testfile():
            comments = []

            fd = open(os.path.join(directory, filename))
            for line in fd:
                line = line.strip()
                if line.startswith('#'):
                    comments.append(line[1:])

            fd.close()

            return comments

        # Get code and description from testfile.
        commands, docstring = self.eval_recusively(filename, directory)

        return Test(filename,
                directory,
                get_title_from_testname(filename),
                docstring,
                get_comments_from_testfile(),
                commands)


class ToHtml(CodeGenerator):
    output_extension = 'html'

    def generate(self, test):
        def htmlize_list(L):
            if not L:
                return ''

            result = ['<ul>']
            for element in L:
                result.append('<li>%s</li>' % element)
            result.append('</ul>')

            return ''.join(result)

        output = []

        output.append(test_template_begin)
        output.append(htmlize_list(test.comments))
        output.append(test_template_mid % test.title)

        for args in test.commands:
            output.append(test_template_test % args)

        output.append(test_template_end)

        return ''.join(output)


class ToPython(CodeGenerator):
    output_extension = 'py'

    def generate(self, test):
        def escape_quote(text):
            return text.replace("'", "\\'")
        def with_quotes(text):
            if '\n' in text or '\r' in text:
                return "'''" + text + "'''"
            return "'" + text + "'"

        content = []

        # Place a module docstring first.
        content.append('"""\n%s\n"""\n\n' % test.description)

        # Then paste a series of commands.
        for comm in test.commands:
            if comm[2] == '':
                if comm[1] == '':
                    content.append("S.%s()\n" % comm[0])
                else:
                    content.append("S.%s(%s)\n" % (comm[0],
                            with_quotes(escape_quote(comm[1]))))
            else:
                content.append("S.%s(%s, %s)\n" %\
                        (comm[0], with_quotes(escape_quote(comm[1])),
                                  with_quotes(escape_quote(comm[2]))))

        return ''.join(content)


################################################################################
#  Parsing infrastructure.
################################################################################

class Test(object):
    def __init__(self, filename, directory, title, description, comments,
                 commands):
        self.filename = filename
        self.directory = directory
        self.title = title
        self.description = description
        self.comments = comments
        self.commands = commands

    def __cmp__(self, other):
        return cmp(self.filename, other.filename)


def make_selenium_one(from_module, to_module, srcfile, destination_file=None):
    imod = from_module()
    omod = to_module()

    filename = os.path.basename(srcfile)
    dirname = os.path.dirname(srcfile)

    # Create Test object from source file.
    test = imod.get_test_from_file(filename, dirname)

    # Create output content by invoking destination module.
    content = omod.generate(test)

    if destination_file is None:
        destination_file = os.path.join(dirname, change_extension(filename, omod.output_extension))

    write_str_to_file(content, destination_file)


def make_selenium(from_module, to_module, srcdir, dstdir):
    imod = from_module()
    omod = to_module()

    if os.access(dstdir, os.F_OK):
        if not os.access(dstdir, os.W_OK):
            print "Error: Destination directory exists and isn't writable."
            sys.exit(1)
    else:
        os.mkdir(dstdir)

    tests = imod.get_tests_from_dir(srcdir)

    # Parse each test in directory.
    for test in tests:
        page = omod.generate(test)
        write_str_to_file(page, os.path.join(dstdir,
                change_extension(test.filename, omod.output_extension)))

    # Make index.html if user have chosen html output.
    if isinstance(omod, ToHtml):
        make_index_html(tests, dstdir, omod.output_extension)


def make_index_html(tests, dstdir, output_extension):
    """Prepare index.html file."""

    # Don't make index.html if list of tests is empty.
    if not tests:
        return

    index = index_template_begin

    for test in tests:
        data = {
            'filename'      : os.path.join(dstdir,
                    change_extension(test.filename, output_extension)),
            'title'         : test.title,
            'description'   : test.description,
        }
        index += index_template_content % data

    index += index_template_end

    write_str_to_file(index, os.path.join(dstdir, 'index.html'))


################################################################################
#  Unit tests.
################################################################################

class DestinationDirExistsTestCase(unittest.TestCase):
    """Do not try to create destination dir if it exist."""
    def setUp(self):
        self.src_dir = tempfile.mkdtemp()
        self.dst_dir = tempfile.mkdtemp()

    def tearDown(self):
        os.rmdir(self.src_dir)
        os.rmdir(self.dst_dir)

    def testThis(self):
        make_selenium(FromPython, ToHtml, self.src_dir, self.dst_dir)


class ParseOnlyFilesTestCase(unittest.TestCase):
    """Script should only parse files in source directory."""
    def setUp(self):
        self.src_dir = tempfile.mkdtemp()

        self.dst_dir = os.path.join(self.src_dir, 'dstdir')
        os.mkdir(self.dst_dir)

        self.test_file = os.path.join(self.src_dir, 'test.py')
        fd = open(self.test_file, 'w')
        fd.close()

    def tearDown(self):
        os.remove(self.test_file)
        os.remove(os.path.join(self.dst_dir, 'test.html'))
        os.remove(os.path.join(self.dst_dir, 'index.html'))
        os.rmdir(self.dst_dir)
        os.rmdir(self.src_dir)

    def testThis(self):
        make_selenium(FromPython, ToHtml, self.src_dir, self.dst_dir)


################################################################################
#  Main.
################################################################################

def usage():
    print """Usage:
    make_selenium.py [-p] source_directory destination_directory
    make_selenium.py [-p] source_file [ destination_file ]"""

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--selftest':
        # Run doctest.
        import doctest
        self = __import__(__name__)
        doctest.testmod(self)

        # Run unittest.
        import tempfile
        sys.argv.pop()
        unittest.main()

    # Get convertion mode.
    modules = ( FromPython, ToHtml )
    if len(sys.argv) >= 2:
        try:
            modules = {
                '-p': ( FromHtml, ToPython ),
            }[sys.argv[1]]
            sys.argv.pop(1)
        except KeyError:
            pass

    # Parse whole directory.
    if len(sys.argv) == 3 and is_dir(sys.argv[1]):
        make_selenium(modules[0], modules[1], sys.argv[1], sys.argv[2])
    # Parse single file.
    elif len(sys.argv) >= 2 and is_file(sys.argv[1]):
        if len(sys.argv) == 3:
            make_selenium_one(modules[0], modules[1], sys.argv[1], sys.argv[2])
        else:
            make_selenium_one(modules[0], modules[1], sys.argv[1])
    # Show help.
    else:
        usage()

