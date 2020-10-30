#!/bin/bash

make_and_keep() {
    mkdir -p "$1"
    touch "$1/.gitkeep"
    git add "$1/.gitkeep"
}

make_and_keep reg/common/package
make_and_keep reg/g/pcds/pyps
make_and_keep reg/g/pcds/package/epics/3.14/ioc
make_and_keep reg/g/pcds/controls/camerecord
make_and_keep reg/d/iocData
make_and_keep reg/d/iocCommon
make_and_keep reg/d/iocCommon/hosts/localhost
make_and_keep reg/g/pcds/pyps/apps/ioc

# For our test environment:
make_and_keep reg/g/pcds/pyps/config/tst

# These are part of submodules - but we want to add on some stuff:
make_and_keep additional_files/reg/d/iocCommon/rhel7-x86_64/facility
