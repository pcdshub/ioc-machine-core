#!/bin/bash
THISHOST=$(hostname -s)

if [ -x /etc/pathinit ]; then
    source /etc/pathinit
else
    export PSPKG_ROOT=/reg/common/package
    export PYPS_ROOT=/reg/g/pcds/pyps
    export IOC_ROOT=/reg/g/pcds/package/epics/3.14/ioc
    export CAMRECORD_ROOT=/reg/g/pcds/controls/camrecord
    export IOC_DATA=/reg/d/iocData
    export IOC_COMMON=/reg/d/iocCommon
fi

if [ -x $IOC_COMMON/hosts/$THISHOST/startup.cmd ]; then
  $IOC_COMMON/hosts/$THISHOST/startup.cmd
  exit 0
fi

if [ -x $IOC_COMMON/rhel7-x86_64/common/startup.cmd ]; then
  $IOC_COMMON/rhel7-x86_64/common/startup.cmd
  exit 0
fi
