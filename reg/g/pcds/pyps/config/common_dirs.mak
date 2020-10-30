#
# common_dirs.mak
#
# Include in make compatible builds via
# -include /reg/g/pcds/pyps/config/common_dirs.mak
#
#  Sets several macros for directory paths
#  that are expected to be shared by many
#  different build systems.
#
FACILITY_ROOT=/reg/g/pcds
CONFIG_SITE_TOP=/reg/g/pcds/pyps/config
CTRL_REPO=file:///afs/slac/g/pcds/vol2/svn/pcds
DATA_SITE_TOP=/reg/d
EPICS_SITE_TOP=/reg/g/pcds/epics
GIT_SITE_TOP=/afs/slac/g/cd/swe/git/repos
GIT_TOP=$GIT_SITE_TOP
GW_SITE_TOP=/reg/g/pcds/gateway
IOC_COMMON=/reg/d/iocCommon
IOC_DATA=/reg/d/iocData
PACKAGE_SITE_TOP=/reg/g/pcds/package
PSPKG_ROOT=/reg/g/pcds/pkg_mgr
PYAPPS_SITE_TOP=/reg/g/pcds/controls
PYPS_SITE_TOP=/reg/g/pcds/pyps
SETUP_SITE_TOP=/reg/g/pcds/setup
EPICS_SETUP=$(SETUP_SITE_TOP)
TOOLS_SITE_TOP=/reg/common/tools

# Deprecated, soon to disappear
EPICS_REPO=file:///afs/slac/g/pcds/vol2/svn/pcds
