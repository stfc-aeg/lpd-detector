import datetime, time

### Create timestamp with seconds in fraction of 9 decimal points
dt = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
tt = time.time()
nanoSeconds = "%2.9f" % (tt - int(tt))
label = dt + nanoSeconds[1:]
print "\nExample of Nanosecond scale time info:"
print "'" + label + "'"
#eg: '0412-13:32:16.266228914'

print "\nSeveral closely linked times:"

ll = []
for idx in range(5):
    dt = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
    tt = time.time()
    nanoSecs = "%2.9f" % (tt - int(tt))
    label = dt + nanoSecs[1:]
    ll.append(label)

#print differences
for idx in range(len(ll)):
    print ll[idx]


print ""
