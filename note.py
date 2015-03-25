#! /usr/bin/env python
import os
import pickle
import argparse
import hashlib
from glob import glob
from patterns import Borg
import parser
import traceback

from pdb import set_trace


class manager(object):
    def __init__(self):
        self.notes = {}
        self.remotes = {}
        parser.addObserver(keyWordsObserver())

    def update(self):
        for r in self.remotes.values():
            for f in glob(os.path.join(r, '*.mino')):
                n = self.notes.get(f)
                if not n:
                    self.notes[f] = note(f)
                else:
                    n.update()

    def flush(self):
        self.notes.clear()

class keyWordsObserver(Borg):
    def update(self, issuer, event, message):
        if event == 'mino/doc/start':
            if isinstance(issuer, parser.mdTitle):
                self.tgt.update(set(issuer.content.lower().split()))

    def setTarget(self, tgt):
        self.tgt = tgt

class note(object):
    def __init__(self, filePath):
        self.filePath = filePath
        self.words = set()  # In case it's requested before update...
        self.cksum = 0
        self.update()
        
    def update(self):
        # Update the note if it has changed
        if self.cksum != self.getHash():
            print '%s has changed, update it\'s metadata' % self.filePath
            # Do long update stuff here
            try:
                doc = parser.load(self.filePath)
                keyWordsObserver().setTarget(self.words)
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
    if args.force:
        mgr.flush()
    mgr.update()

def call_add(mgr, args):
    pass

def call_remove(mgr, args):
    pass

def call_list(mgr, args):
    print '\n  '.join(f for f in mgr.notes.keys())

def call_search(mgr, args):
    pass

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
    parser_update.set_defaults(func=call_update)


    parser_add = subparsers.add_parser('add')
    # Store which function to call after the parsing is done (tip given by python.org)
    parser_add.set_defaults(func=call_add)

    parser_remove = subparsers.add_parser('remove')
    parser_remove.set_defaults(func=call_remove)

    parser_list = subparsers.add_parser('list')
    parser_list.set_defaults(func=call_list)

    parser_search = subparsers.add_parser('search')
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



