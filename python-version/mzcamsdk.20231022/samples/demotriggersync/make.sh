#!/bin/bash
os=`uname -s`
if [[ $os = "Linux" ]]; then
	g++ -Wl,-rpath -Wl,'$ORIGIN' -L. -g -o demotriggersync demotriggersync.cpp -lmzcam
else
	clang++ -Wl,-rpath -Wl,. -L. -g -o demotriggersync demotriggersync.cpp -lmzcam
fi
