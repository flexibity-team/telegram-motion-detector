import hashlib

import sys
import os

stdin = sys.stdin
#salt = os.urandom(16)

print 'enter password:'
password = stdin.readline()

m = hashlib.md5()
m.update(password)
print 'hash is: ' + m.hexdigest()
