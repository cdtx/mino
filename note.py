#! /usr/bin/env python
import os, re
import string
import pickle
import argparse
import hashlib
from glob import glob
import parser, observers
import traceback
import subprocess
from datetime import datetime
import tempfile
import webbrowser

from pdb import set_trace


class manager(object):
    def __init__(self):
        # {(<remote>,<note_name>) : <note object>}
        self.notes = {}
        # {<remote name> : <remote path>}
        self.remotes = {}

    def update(self, remote=None):
        for (k,v) in self.remotes.iteritems():
            if remote and remote != v:
                continue
            for f in glob(os.path.join(v, '*.mino')):
                n = self.notes.get((k,f))
                if not n:
                    n = note(f)
                    n.update()
                    self.notes[(k,f)] = n
                else:
                    n.update()

    def flush(self, remote=None):
        if not remote:
            self.notes.clear()
        else:
            for x in self.notes.keys():
                if x[0] == remote:
                    self.notes.pop(x)


class keyWordsObserver(object):
    def __init__(self, tgt):
        self.tgt = tgt

    def update(self, issuer, event, message):
        if event == 'mino/doc/start':
            if (isinstance(issuer, parser.mdTitle)) or (isinstance(issuer, parser.mdTextLine)):
                # Remove punctuation, set to lower, then split
                self.tgt.update(set(re.split(r'[ /.=,;:!?(){}[]|]', issuer.content.lower())))


class note(object):
    def __init__(self, filePath):
        self.filePath = filePath
        self.words = set()  # In case it's requested before update...
        self.cksum = 0

    @staticmethod
    def create(path, name=None):
        # If not specified, generate a name
        currentTime = datetime.now()
        # Note name <year><month><day>_<hour><minute>.mino
        name = '%.4d%.2d%.2d_%.2d%.2d.mino' % (currentTime.year, currentTime.month, currentTime.day, currentTime.hour, currentTime.minute)
        notePath = os.path.join(path, name)
        if not os.path.exists(notePath):
            return note(notePath)
        else:
            raise Exception('Note path already exists (%s)'%notePath)

        
    def update(self):
        # Update the note if it has changed
        if self.cksum != self.getHash():
            print '%s has changed, update it\'s metadata' % self.filePath
            # Do long update stuff here
            try:
                doc = parser.load(self.filePath)
                doc.addObserver(keyWordsObserver(self.words))
                doc.doc()
                self.cksum = self.getHash()
            except:
                print 'Failed parsing %s' % self.filePath
                print traceback.format_exc()

    def getHash(self):
        with open(self.filePath, 'rb') as file:
            hasher = hashlib.sha256()
            buf = file.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = file.read(65536)
            return hasher.digest()

    def edit(self):
        try:
            print 'Editing %s' % str(self.filePath)
            callArgs = ['gvim', self.filePath]
            subprocess.Popen(callArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        except:
            print 'Invalid edition request'

    def createHTML(self, fileName=None, openAfter=False):
        '''
        If a file name is specified, just create it, else create a random tmp file then invoke the browser to open it.        
        '''
        try:
            # Plug html observer
            doc = parser.load(self.filePath)
            obs = observers.HtmlDocObserver(localRessources=True)
            doc.addObserver(obs)
            doc.doc()
            if not fileName:
                tmpFile = tempfile.NamedTemporaryFile(suffix='.html')
                fileName = tmpFile.name
                tmpFile.close()
            obs.toFile(fileName)
            if openAfter:
                webbrowser.open('file:///' + os.path.abspath(fileName))
        except Exception as e :
            print 'An error occurs, cannot serve', e

    def __str__(self):
        str = '%s - %s' % (self.filePath, self.cksum)
        return str

class todo(note):
    pass


def db_open():
    if not os.environ.has_key('MINO_DATABASE_PATH'):
        raise Exception('Cannot locate database, set MINO_DATABASE_PATH before')
    
    # Does the database exist
    mgr = manager()
    if os.path.exists(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbNotes')):
        with open(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbNotes'), 'r') as file:
            mgr.notes = pickle.load(file)

    if os.path.exists(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbRemotes')): 
        with open(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbRemotes'), 'r') as file:
            mgr.remotes = pickle.load(file)

    return mgr


def db_save(mgr):
    with open(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbNotes'), 'w') as file:
        pickle.dump(mgr.notes, file)
    with open(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbRemotes'), 'w') as file:
        pickle.dump(mgr.remotes, file)

def db_close(mgr):
    pass

def call_update(mgr, args):
    remote = args.remote
    if args.force:
        mgr.flush(remote)
    mgr.update(remote)

def call_add(mgr, args):
    if len(mgr.remotes) == 1:
        # If one remote only, use it, ignoring the --remote param
        remote = mgr.remotes[mgr.remotes.keys()[0]]

    if len(mgr.remotes) > 1 and not args.remote:
        raise Exception('No remote specified')

    if args.remote :
        remote = mgr.remotes.get(args.remote, None)

    if not remote:
        raise Exception('Invalid remote')

    # Create note
    note.create(remote).edit()



def call_remove(mgr, args):
    pass

def call_list(mgr, args):
    print '\n'.join('-'.join(f) for f in mgr.notes.keys() if (not args.remote or f[0]==args.remote))


class printTitleAndKeywordsMatchingObserver(object):
    def __init__(self, words):
        self.words = words
        self.somethingFound = False

    def update(self, issuer, event, message):
        if event == 'mino/doc/start':
            if isinstance(issuer, parser.mdDocumentTitle):
                print '\t',issuer.content
            if isinstance(issuer, parser.mdTitle) or isinstance(issuer, parser.mdTextLine) or isinstance(issuer, parser.mdListItem):
                # If one of the searched words in in the content
                if filter(lambda x: x in issuer.content.lower(), self.words):
                    self.somethingFound = True
                    print '\t\t'+issuer.content
        elif event == 'mino/doc/stop':
            if isinstance(issuer, parser.mdRootDoc):
                if self.somethingFound:
                    print ''



def call_search(mgr, args):
    matching = []
    for (k,v) in mgr.notes.iteritems():
        # Is this remote to be part of the search
        if args.remote and not k[0]==args.remote:
            continue
        # Are the given words part of the whole words of a note
        toFind = set(map(str.lower, args.words))
        if toFind.issubset(v.words):
            matching.append(v)
            # If so, print the note, then the extract where the words where found
            print matching.index(v), k
            doc = parser.load(v.filePath)
            doc.addObserver(printTitleAndKeywordsMatchingObserver(toFind))
            doc.doc()
            print ''

    # If an edition is requested
    if args.edit != None:
        matching[args.edit].edit()
    if args.view != None:
        matching[int(args.view[0])].createHTML(args.view[1], openAfter=True)
    if args.export != None:
        matching[int(args.export[0])].createHTML(args.export[1], openAfter=False)

def call_remote_add(mgr, args):
    if not args.name:
        raise Exception('No name given')
    if not args.url:
        raise Exception('No url given')

    if os.path.realpath(args.url) in mgr.remotes.values():
        raise Exception('This url (%s) is already in the remotes list' % os.path.realpath(args.url))

    mgr.remotes[args.name] = os.path.realpath(args.url)

def call_remote_remove(mgr, args):
    if not args.name:
        raise Exception('No name given')
    if not mgr.remotes.has_key(args.name):
        raise Exception('%s is not a known remote name' % args.name)
    mgr.remotes.pop(args.name)

def call_remote_list(mgr, args):
    print '\n'.join('%s  %s' % (x, y) for (x,y) in mgr.remotes.iteritems())


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
                description='Command line interface for powerfull notes and todos managment',        
            
    )

    subparsers = arg_parser.add_subparsers()

    parser_update = subparsers.add_parser('update')
    parser_update.add_argument('--force', action='store_true', help='Force all notes updates')
    parser_update.add_argument('--remote',  help='Specify a unique remote to work with (default all)')
    parser_update.set_defaults(func=call_update)


    parser_add = subparsers.add_parser('add')
    # Store which function to call after the parsing is done (tip given by python.org)
    parser_add.add_argument('--remote',  help='Specify a unique remote to work with (default all)')
    parser_add.set_defaults(func=call_add)

    parser_remove = subparsers.add_parser('remove')
    parser_remove.set_defaults(func=call_remove)

    parser_list = subparsers.add_parser('list')
    parser_list.add_argument('--remote',  help='Specify a unique remote to work with (default all)')
    parser_list.set_defaults(func=call_list)

    parser_search = subparsers.add_parser('search')
    parser_search.add_argument('--remote',  help='Specify a unique remote to work with (default all)')
    parser_search.add_argument('words', type=str, nargs='*', help='The words to look for, can be empty for listing the whole notes')
    parser_search.add_argument('--edit', type=int, const=0, nargs='?', help='Open the first or specified note in the default text editor')
    parser_search.add_argument('--view', nargs=2, help='Open the specified note in the default webbrowser')
    parser_search.add_argument('--export', nargs=2, help='Creates a single html file for this note')
    parser_search.set_defaults(func=call_search)

    # The remote parser
    parser_remote = subparsers.add_parser('remote')
    subparsers_remote = parser_remote.add_subparsers()

    parser_remote_add = subparsers_remote.add_parser('add')
    parser_remote_add.add_argument('name', type=str)
    parser_remote_add.add_argument('url', type=str)
    parser_remote_add.set_defaults(func=call_remote_add)

    parser_remote_remove = subparsers_remote.add_parser('remove')
    parser_remote_remove.add_argument('name', type=str)
    parser_remote_remove.set_defaults(func=call_remote_remove)

    parser_remote_list = subparsers_remote.add_parser('list')
    parser_remote_list.set_defaults(func=call_remote_list)

    # Open the database
    mgr = db_open()
    mgr.update()
    #-----------------------------------

    args = arg_parser.parse_args()
    args.func(mgr, args)

    #-----------------------------------
    # Save and close the database
    db_save(mgr)
    db_close(mgr)



