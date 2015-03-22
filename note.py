#! /usr/bin/env python
import os
import pickle
from argparse import ArgumentParser


class manager(object):
    def __init__(self):
        self.remotes = []

    def addNote(self):
        self.remotes.append('a')
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


if __name__ == '__main__':
    actionList = ['note', 'todo', 'remote']

    parser = ArgumentParser()
    parser.add_argument(dest='target', type=str, choices=actionList)

    args = parser.parse_args()
    
    mgr = db_open()

    mgr.addNote()


    db_save(mgr)
    db_close(mgr)



