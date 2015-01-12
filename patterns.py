
class Singleton:
    '''
    Looks like the most official implementation of the singleton pattern
    '''
    __single = None
    def __init__( self ):
        if Singleton.__single:
            raise Singleton.__single
        Singleton.__single = self 

class Borg(object):
    '''
    Looks like the most powerfull implementation of the singleton pattern
    '''
	__state = {}
	def __init__(self):
		self.__dict__ = self.__state
        
