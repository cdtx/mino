#! /usr/bin/env python
import os
import pickle
import argparse
import hashlib
from glob import glob


class manager(object):
    def __init__(self):
        self.notes = {}
        self.remotes = set()

    def update(self):
        for r in self.remotes:
            for f in glob(os.path.join(r, '*.mino')):
                n = self.notes.get(f)
                if not n:
                    self.notes[f] = note(f)
                else:
                    n.update()


class note(object):
    def __init__(self, filePath):
        self.filePath = filePath
        self.words = set()  # In case it's requested before update...
        self.cksum = 0
        
    def update(self):
        if self.cksum != self.getHash():
            # Do long update stuff here
            with open(self.filePath, 'r') as file:
                self.words = set(file.read().split())

            self.cksum = self.getHash()

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



def call_add(mgr, args):
    pass

def call_remove(mgr, args):
    pass

def call_list(mgr, args):
    pass

def call_search(mgr, args):
    pass

def call_remote_add(mgr, args):
    if not args.path:
        raise Exception('Give the path you want to add with --path')
    mgr.remotes.add(os.path.realpath(args.path))

def call_remote_remove(mgr, args):
    if not args.path:
        raise Exception('Give the path you want to remove with --path')
    mgr.remotes.remove(os.path.realpath(args.path))

def call_remote_list(mgr, args):
    print '\n'.join(x for x in mgr.remotes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description='Command line interface for powerfull notes and todos managment',        
            
    )
    subparsers = parser.add_subparsers()

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
    parser_remote_add.add_argument('path', type=str)
    parser_remote_add.set_defaults(func=call_remote_add)

    parser_remote_remove = subparsers_remote.add_parser('remove')
    parser_remote_remove.add_argument('path', type=str)
    parser_remote_remove.set_defaults(func=call_remote_remove)

    parser_remote_list = subparsers_remote.add_parser('list')
    parser_remote_list.set_defaults(func=call_remote_list)

    # Open the database
    mgr = db_open()
    mgr.update()
    #-----------------------------------

    args = parser.parse_args()
    args.func(mgr, args)

    #-----------------------------------
    # Save and close the database
    db_save(mgr)
    db_close(mgr)



