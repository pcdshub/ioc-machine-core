#
# common_dirs.sh
#
# Source in sh compatible login scripts
# such as ~/.profile or ~/.bashrc to define commonly used
# site specific directory paths.
#  Example:
#  source /reg/g/pcds/pyps/config/common_dirs.sh
#
#  This file should not specify version numbers,
#  as choices about which versions of a specific
#  package to use should be handled by setup scripts
#  under $SETUP_SITE_TOP
#
export FACILITY_ROOT=/reg/g/pcds
export CONFIG_SITE_TOP=/reg/g/pcds/pyps/config
export CTRL_REPO=file:///afs/slac/g/pcds/vol2/svn/pcds
export DATA_SITE_TOP=/reg/d
export EPICS_SITE_TOP=/reg/g/pcds/epics
export GIT_SITE_TOP=/afs/slac/g/cd/swe/git/repos
export GIT_TOP=$GIT_SITE_TOP
export GW_SITE_TOP=/reg/g/pcds/gateway
export IOC_COMMON=/reg/d/iocCommon
export IOC_DATA=/reg/d/iocData
export PACKAGE_SITE_TOP=/reg/g/pcds/package
export PSPKG_ROOT=/reg/g/pcds/pkg_mgr
export PYAPPS_SITE_TOP=/reg/g/pcds/controls
export PYPS_SITE_TOP=/reg/g/pcds/pyps
export SETUP_SITE_TOP=/reg/g/pcds/setup
export EPICS_SETUP=$SETUP_SITE_TOP
export TOOLS_SITE_TOP=/reg/common/tools

# Deprecated, soon to disappear
export EPICS_REPO=file:///afs/slac/g/pcds/vol2/svn/pcds
export PYPS_ROOT=$PYPS_SITE_TOP
