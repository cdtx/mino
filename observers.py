import re

class DumbObserver:
    def update(self, issuer, event, message):
        print issuer, event, message