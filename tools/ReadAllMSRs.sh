#!/bin/bash
# Intel makes no useful guarantees on MSR index ranges....
# 
# Observations:
#   a. All architectural MSRs are either in the range 0x0..0xFFF (decimal 4095)
#      or in the range 0xc0000080 .. 0xc0000103
#   b. Some older processors use funny ranges:
#      Xeon 7400 uses 0x107cc to 0x107d8
#	   Xeon Processor MP with L3 cache uses 0x107cc to 0x107d3
#	   Xeon 7100 uses 0x107cc to 0x107d3
#   c. Some newer processors use funny ranges:
#      Tremont uses 0x1309 .. 0x14c8
# Conclusion:
#   Use 0x0..0xfff and 0xc0000080..0xc0000103
# This is a total of 4228 invocations of the rdmsr executable.
# The number of lines of output will depend on how many MSRs are readable.
# Sample output from the Stampede2 test1 cluster
#   c591-101.stampede2:~/tmp:2020-03-25T17:08:13 $ time ~/bin/ReadAllMSRs.sh > /tmp/mccalpin.MSR
#   real	0m9.089s
#   user	0m4.134s
#   sys	0m4.495s
#   c591-101.stampede2:~/tmp:2020-03-25T17:08:36 $ wc -l /tmp/mccalpin.MSR 
#   1106 /tmp/mccalpin.MSR
MIN_SMALL_MSR=0
MAX_SMALL_MSR=$(( 0xfff ))
MIN_LARGE_MSR=$(( 0xc0000080 ))
MAX_LARGE_MSR=$(( 0xc0000103 ))
for MSR in `seq $MIN_SMALL_MSR $MAX_SMALL_MSR` `seq $MIN_LARGE_MSR $MAX_LARGE_MSR`
do
	XMSR=`printf "0x%.8x" $MSR`
	RETURN=`/home1/06280/mcawood/scratch/rdmsr -p 0 -x -0 $XMSR 2>&1`
	if [ $? -eq 0 ]
	then
		echo "$XMSR $RETURN"
	#else
	#	echo "$XMSR NotReadable"
	fi
done
