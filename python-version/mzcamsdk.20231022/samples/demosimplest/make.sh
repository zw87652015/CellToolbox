#!/bin/bash
os=`uname -s`
if [[ $os = "Linux" ]]; then
	g++ -Wl,-rpath -Wl,'$ORIGIN' -L. -g -o demosimplest demosimplest.cpp -lmzcam
else
	clang++ -Wl,-rpath -Wl,. -L. -g -o demosimplest demosimplest.cpp -lmzcam
fi
