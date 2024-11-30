#!/bin/bash

for d in ./tasksets/80-percent/*; do
    for a in dm edf rr; do
        python ./src/plot.py $a ./tasksets/80-percent/$d
    done
done

for d in ./tasksets/10-tasks/*; do
    for a in dm edf rr; do
        python ./src/plot.py $a ./tasksets/10-tasks/$d
    done
done