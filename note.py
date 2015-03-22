#! /usr/bin/env python
import os
import pickle
import argparse


class manager(object):
    def __init__(self):
        self.remotes = {}

    def addNote(self):
        pass


class note(object):
    def __init__(self):
        fileName = ''

class todo(note):
    pass


def db_open():
    if not os.environ.has_key('MINO_DATABASE_PATH'):
        raise Exception('Cannot locate database, set MINO_DATABASE_PATH before')
    
    # Does the database exist
    if not os.path.exists(os.environ['MINO_DATABASE_PATH']):
        print 'Database not found, create one'
        mgr = manager()
    else:
        print 'Database found at %s, open it' % os.environ['MINO_DATABASE_PATH']
        with open(os.environ['MINO_DATABASE_PATH'], 'r') as file:
            mgr = pickle.load(file)

    return mgr

def db_save(mgr):
    with open(os.environ['MINO_DATABASE_PATH'], 'w') as file:
        pickle.dump(mgr, file)
    pass

def db_close(mgr):
    pass


def call_note(mgr, args):
    pass

def call_remote(mgr, args):
    if args.action == 'add': 
        if not args.path:
            raise Exception('Give the path you want to add with --path')
        mgr.remotes.append(args.path)
    if args.action == 'remove': 
        if not args.path:
            raise Exception('Give the path you want to remove with --path')
        mgr.remotes.remove(args.path)
    elif args.action == 'list':
        print mgr.remotes


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

    
    # Open the database
    mgr = db_open()
    #-----------------------------------

    args = parser.parse_args()
    args.func(mgr, args)

    #-----------------------------------
    # Save and close the database
    db_save(mgr)
    db_close(mgr)



