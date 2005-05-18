# Copyright (C) 2005 Aaron Bentley and Panometrics, Inc.
# <abentley@panoramicfeedback.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
from popen2 import Popen3
import os
import config
client = config.get_val("arch_client")
if client is None:
    client = "tla"
    config.set_val("arch_client", client)

def invoke(args):
    q=Popen3(args, True)
    output = q.fromchild.read()
    error = q.childerr.read()
    status = q.wait()
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status), output, error
    raise Exception("Command failed: %s" % error)

def invoke_client(*args, **kwargs):
    cl_args = [client]
    cl_args.extend(args)
    status,output,error = invoke(cl_args)
    if status not in (0,):
        raise Exception("Command failed: %s" % error)
    return output

def write_tree_settings(contents, path):
    file(os.path.join(path, "{arch}", "=tagging-method"), "wb").write(contents)

def init_tree(path):
    invoke_client("init-tree", "-d", path)

def temp_arch_tree(type="easy"):
    import tempfile
    path = tempfile.mkdtemp()
    init_tree(path)
    if type=="easy":
        write_tree_settings("source ^.*$\n", path)
    elif type=="tricky":
        write_tree_settings("source ^$\n", path)
    else:
        assert (type=="impossible")
        add_dir_rule("precious ^\.boo$", path, path)
    return path

def list_added(root):
    assert os.path.exists(root)
    assert os.access(root, os.X_OK)
    root = os.path.realpath(root)
    inv_str = invoke_client("inventory", "--source", '--both', '--all', root)
    return [os.path.join(root, p) for p in inv_str.split('\n')]

def tree_root(filename):
    assert os.path.exists(filename)
    if not os.path.isdir(filename):
        dirname = os.path.dirname(filename)
    else:
        dirname = filename
    return invoke_client("tree-root", dirname).rstrip('\n')

def rel_filename(filename, root):
    assert(filename.startswith(root))
    return filename[len(root)+1:]

class CantAddFile(Exception):
    def __init__(self, file):
        self.file = file
        Exception.__init__(self, "Can't automatically add file %s" % file)
    

def add_dir_rule(rule, dirname, root):
    inv_filename = os.path.join(dirname, '.arch-inventory')
    file(inv_filename, "ab").write(rule)
    if os.path.realpath(inv_filename) not in list_added(root):
        add_id(inv_filename, no_force=True)

def force_source(filename, root):
    rule = "source %s\n" % rel_filename(filename, root)
    add_dir_rule(rule, os.path.dirname(filename), root)
    if os.path.realpath(filename) not in list_added(root):
        raise CantAddFile(filename)

def add_id(filename, no_force=False):
    invoke_client("add-id", filename)
    root = tree_root(filename)
    if os.path.realpath(filename) not in list_added(root) and not no_force:
        force_source(filename, root)


def delete_id(filename):
    invoke_client("delete-id", filename)

def test_helper(type):
    t = temp_arch_tree(type)
    dirname = os.path.join(t, ".boo")
    return dirname, t

def mkdir(path):
    """
    >>> import shutil
    >>> dirname,t = test_helper("easy")
    >>> mkdir(dirname)
    >>> assert os.path.realpath(dirname) in list_added(t)
    >>> assert not os.path.exists(os.path.join(t, ".arch-inventory"))
    >>> shutil.rmtree(t)
    >>> dirname,t = test_helper("tricky")
    >>> mkdir(dirname)
    >>> assert os.path.realpath(dirname) in list_added(t)
    >>> assert os.path.exists(os.path.join(t, ".arch-inventory"))
    >>> shutil.rmtree(t)
    >>> dirname,t = test_helper("impossible")
    >>> try:
    ...     mkdir(dirname)
    ... except CantAddFile, e:
    ...     print "Can't add file"
    Can't add file
    >>> shutil.rmtree(t)
    """
    os.mkdir(path)
    add_id(path)

def set_file_contents(path, contents):
    add = not os.path.exists(path)
    file(path, "wb").write(contents)
    if add:
        add_id(path)


def path_in_reference(bug_dir, spec):
    if spec is not None:
        return invoke_client("file-find", bug_dir, spec).rstrip('\n')
    return invoke_client("file-find", bug_dir).rstrip('\n')


def unlink(path):
    try:
        os.unlink(path)
        delete_id(path)
    except OSError, e:
        if e.errno != 2:
            raise


def detect(path):
    """Detect whether a directory is revision-controlled using Arch"""
    path = os.path.realpath(path)
    while True:
        if os.path.exists(os.path.join(path, "{arch}")):
            return True
        if path == "/":
            return False
        path = os.path.dirname(path)


name = "Arch"
