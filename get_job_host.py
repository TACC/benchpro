

line1="             JOBID   PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)"
line2="           5665640       test1 idv41950  mcawood  R       1:42      1 c591-101"

pos = line1.find("NODELIST")

print(line2[pos:])

