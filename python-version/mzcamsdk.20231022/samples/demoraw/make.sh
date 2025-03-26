#!/bin/bash
os=`uname -s`
if [[ $os = "Linux" ]]; then
	g++ -Wl,-rpath -Wl,'$ORIGIN' -L. -g -o demoraw demoraw.cpp -lmzcam -lncurses
else
	clang++ -Wl,-rpath -Wl,. -L. -g -o demoraw demoraw.cpp -lmzcam -lncurses
fi
