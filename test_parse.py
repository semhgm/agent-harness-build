from v7 import parseArgs

print(parseArgs('{"fileName": "a.txt"}'))   # ({'fileName': 'a.txt'}, None)
print(parseArgs('{"fileName": "a.txt"'))    # (None, 'Invalid JSON ...')
print(parseArgs('[]'))                       # (None, 'Tool arguments must be ...')
print(parseArgs(None))                      # ({}, None)
print(parseArgs(''))   