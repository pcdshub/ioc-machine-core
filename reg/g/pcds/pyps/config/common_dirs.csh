#
# common_dirs.csh
#
# Source in csh compatible login scripts
# such as ~/.cshrc or ~/.tcshrc to define
# commonly used # site specific directory paths.
#  Example:
#  source /reg/g/pcds/pyps/config/common_dirs.csh
#
#  This file should not specify version numbers,
#  as choices about which versions of a specific
#  package to use should be handled by setup scripts
#  under $SETUP_SITE_TOP
#
setenv FACILITY_ROOT /reg/g/pcds
setenv CONFIG_SITE_TOP /reg/g/pcds/pyps/config
setenv CTRL_REPO file:///afs/slac/g/pcds/vol2/svn/pcds
setenv DATA_SITE_TOP /reg/d
setenv EPICS_SITE_TOP /reg/g/pcds/epics
setenv GIT_SITE_TOP /afs/slac/g/cd/swe/git/repos
setenv GIT_TOP $GIT_SITE_TOP
setenv GW_SITE_TOP /reg/g/pcds/gateway
setenv IOC_COMMON /reg/d/iocCommon
setenv IOC_DATA /reg/d/iocData
setenv PACKAGE_SITE_TOP /reg/g/pcds/package
setenv PSPKG_ROOT /reg/g/pcds/pkg_mgr
setenv PYAPPS_SITE_TOP /reg/g/pcds/controls
setenv PYPS_SITE_TOP /reg/g/pcds/pyps
setenv SETUP_SITE_TOP /reg/g/pcds/setup
setenv EPICS_SETUP $SETUP_SITE_TOP
setenv TOOLS_SITE_TOP /reg/common/tools

# Deprecated, soon to disappear
setenv EPICS_REPO file:///afs/slac/g/pcds/vol2/svn/pcds
setenv PYPS_ROOT $PYPS_SITE_TOP
