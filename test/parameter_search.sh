#!/bin/bash
# search the entropy threshold and bits per pixel parameter space
# for good values for an image and compression level
nrounds=10
padlen=${#nrounds}
bitsmin=1
bitsmax=63
threshmin=10000
threshmax=250000
threshpad=${#threshmax}
threshstep=10000
outputtype="jpeg"
quality="95"

resultsdir=et_results/tornado

runtest() {
    datasize=$1
    printf $'.PHONY: out\n'
    for (( thresh = threshmin; thresh <= threshmax; thresh += threshstep )); do
        for (( bits = bitsmin; bits < bitsmax+1; bits++ )); do
            printf $'out: out.%u.%u\n' $bits $thresh
            printf $'out.%u.%u:\n' $bits $thresh
            printf $'\tpython EntropyTest.py ../images/resubmission/streamlines/xy_150-250.0000.0.4.png -b %s -e %s -n %s -d %d -t %s -q %s --quiet; echo $$? > $@\n' \
                $bits $thresh $nrounds $datasize $outputtype $quality
        done
    done
}

for datasize in 16 32 128 1024; do
    make -j 48 -f <( runtest $datasize ) out

    qdir="$resultsdir/$outputtype/$quality"
    fname="$qdir/d$datasize.txt"
    mkdir -p $qdir

    # header
    s=" "
    printf $'%*s ' $threshpad $s > $fname
    for (( bits = bitsmin; bits < bitsmax+1; bits++ )); do
        printf $'%*u ' $padlen $bits >> $fname
    done
    printf '\n' >> $fname

    for (( thresh = threshmin; thresh <= threshmax; thresh += threshstep )); do
        printf $'%*u ' $threshpad $thresh >> $fname
        for (( bits = bitsmin; bits < bitsmax+1; bits++ )); do
            printf $'%*u ' $padlen $(cat out.$bits.$thresh) >> $fname
        done
        printf $'\n' >> $fname
    done
    rm out.*
done
