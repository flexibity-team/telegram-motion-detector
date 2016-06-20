import hashlib

import sys
import os

stdin = sys.stdin
#salt = os.urandom(16)

print 'enter password:'
password = stdin.readline().split('\n')[0]

m = hashlib.md5()
m.update(password)
print 'hash for ' + password + ' (' + `len(password)` + ') is: ' + m.hexdigest()
