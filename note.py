#! /usr/bin/env python
import os
import pickle
import argparse
import hashlib
from glob import glob


class manager(object):
    def __init__(self):
        self.remotes = set()

    def update(self):
        for r in self.remotes:
            for f in glob(os.path.join(r, '*.mino')):
                self.addNote(note(f))

    def addNote(self, aNote):
        print aNote

class note(object):
    def __init__(self, filePath):
        self.filePath = filePath
        self.cksum = self.hashfile(self.filePath)
        
    def hashfile(self, aFilePath):
        with open(aFilePath, 'rb') as file:
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
    if not os.path.exists(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbNotes')):
        print 'Database not found, create one'
        mgr = manager()
    else:
        with open(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbNotes'), 'r') as file:
            mgr = pickle.load(file)

    if os.path.exists(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbRemotes')): 
        with open(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbRemotes'), 'r') as file:
            mgr.remotes = pickle.load(file)

    return mgr


def db_save(mgr):
    with open(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbNotes'), 'w') as file:
        pickle.dump(mgr, file)
    with open(os.path.join(os.environ['MINO_DATABASE_PATH'], 'dbRemotes'), 'w') as file:
        pickle.dump(mgr.remotes, file)

def db_close(mgr):
    pass


def call_note(mgr, args):
    pass

def call_remote(mgr, args):
    if args.action == 'add': 
        if not args.path:
            raise Exception('Give the path you want to add with --path')
        mgr.remotes.add(os.path.realpath(args.path))
    if args.action == 'remove': 
        if not args.path:
            raise Exception('Give the path you want to remove with --path')
        mgr.remotes.remove(os.path.realpath(args.path))
    elif args.action == 'list':
        print mgr.remotes

def call_update(mgr, args):
     mgr.update()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description='Command line interface for powerfull notes and todos managment',        
            
    )
    subparsers = parser.add_subparsers()

    # The note parser
    parser_note = subparsers.add_parser('note')
    parser_note.add_argument(dest='action', type=str, choices=['add'])
    # Remember which function to call after the parsing is done (tip given by python.org)
    parser_note.set_defaults(func=call_note)


    # The remote parser
    parser_remote = subparsers.add_parser('remote')
    parser_remote.add_argument(dest='action', type=str, choices=['add', 'remove', 'list'])
    parser_remote.add_argument('--path', type=str)
    parser_remote.set_defaults(func=call_remote)

    parser_remote = subparsers.add_parser('update')
    parser_remote.set_defaults(func=call_update)
    
    # Open the database
    mgr = db_open()
    #-----------------------------------

    args = parser.parse_args()
    args.func(mgr, args)

    #-----------------------------------
    # Save and close the database
    db_save(mgr)
    db_close(mgr)



