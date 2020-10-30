PCDS IOC Machine Core
=====================

Purpose: document the entire IOC boot process

Assumptions: 
* `rhel7-x86_64`-based machine

System Settings
===============

IOC machine provisioning
------------------------

### Puppet

Machines provisioned by way of puppet:

https://pswww.slac.stanford.edu/pcds/git/PCDS/Puppet_Files

Per-node manifests are specified here:

https://pswww.slac.stanford.edu/pcds/git/PCDS/Puppet_Files/src/branch/master/manifests/nodes

Which reference individual modules, indicating how to install the given packages:

https://pswww.slac.stanford.edu/pcds/git/PCDS/Puppet_Files/src/branch/master/modules

### Additional files

The vast majority of files are located in shared spaces: AFS/NFS and now WEKA as of October 2020.
Some files, such as those used for IOC startup systemd scripts may come from PCDS IT-generated 
images.

Startup
-------

### procmgrd.service

If configured, this will start the process manager daemon after
`multi-user.target` (run level 2).

This spawns 8 processes, serving platforms 0 through 7.

However, this appears to not be configured for some machines (such as
`ioc-lfe-srv01`).

#### Configuration: `/etc/procmgrd.conf`

Variables:
* `PORTBASE`: starting port number
* `PROCMGRDBIN`: binary directory
* `PROCMGRDUSER`: user to run procmgrd as

Port numbers, per platform:
* Control port: `PORTBASE + 100 * [0..7]`
* Log port: `control_port + 1`


### ioc.service

This service is configured to run after `multi-user.target` (run level 2),
executing this bash script:
[/usr/lib/systemd/scripts/ioc.sh](/usr/lib/systemd/scripts/ioc.sh).

It is configured on `ioc-kfe-srv01` and others I've checked.

It does not require additional machine-level configuration, as it relies on
scripts on a shared filesystem, notably those in `$IOC_COMMON`
(`/reg/d/iocCommon`).

#### Steps

1. Use paths from `/etc/pathinit` or fall back to defaults in `ioc.sh`
2. If it exists, execute `$IOC_COMMON/hosts/$(hostname -s)/startup.cmd` and exit.
3. If it exists, execute `$IOC_COMMON/rhel7-x86_64/common/startup.cmd ` and exit.
4. Otherwise, do nothing.


#### Common startup.cmd

Prerequisites:
* Ran as root

Variables:
* Sets `T_A` (target architecture)
* Sets `PYPS_ROOT` to `$PYPS_SITE_TOP` (back-compat)

##### Steps

1. Source common directories scripts [/reg/g/pcds/pyps/config/common_dirs.sh](/reg/g/pcds/pyps/config/common_dirs.sh).
2. If it exists, source common settings for the architecture: 
    [$IOC_COMMON/$T_A/facility/ioc_env.sh](/additional_files/reg/d/iocCommon/rhel7-x86_64/facility/ioc_env.sh)
    * Copy it over to `/etc/profile.d/ioc_env.sh`
    * Ensure it's executable
3. Set the location for core files (`/tmp`)
4. Set process level limits (unlimited core size, locked memory, and real-time
   scheduling priority)
5. Load any kernel modules necessary [/reg/d/iocCommon/rhel7-x86_64/common/kernel-modules.cmd](/reg/d/iocCommon/rhel7-x86_64/common/kernel-modules.cmd)
6. Finally, launch IocManager by way of [/reg/g/pcds/pyps/apps/ioc/latest/initIOC](https://github.com/pcdshub/IocManager/blob/master/initIOC)
7. (See next section regarding initIOC.)


initIOC
-------

This script is part of the [IocManager](https://github.com/pcdshub/IocManager)
repository and can be found here: 
[/reg/g/pcds/pyps/apps/ioc/latest/initIOC](https://github.com/pcdshub/IocManager/blob/master/initIOC)

### Prerequisites
* Run as root
* Package `controls-basic-0.0.1` exists.

### Steps

1. Set variables, if not previously set
    * `PYPS_ROOT=/reg/g/pcds/pyps`
    * `PSPKG_ROOT=/reg/g/pcds/pkg_mgr`
    * `PSPKG_RELEASE=controls-basic-0.0.1`
2. Check the hostname, and determine the configuration directory to use.
    * The configuration directory is: `$PYPS_ROOT/config/${cfg}/iocmanager`
    * The hostname is expected to follow the format `ioc-XYZ-something`, such
      that in this example `cfg` would be `XYZ`.  It does not intelligently
      parse this - it must be 3 characters in that specific location.
    * To override this default, a mapping file can be used:
      [$PYPS_ROOT/config/hosts.special](/reg/g/pcds/pyps/config/hosts.special)
      This file contains two columns `$(hostname -s)    CFG`.
3. Set variables now that the configuration path is known:
    * Sets `SCRIPTROOT=$PYPS_ROOT/config/$cfg/iocmanager`
    * Sources `$PSPKG_ROOT/etc/set_env.sh` (to use `controls-basic-0.0.1`
      binaries and scripts)
    * Updates `$PATH` to include the IocManager script root (e.g.,
      [/reg/g/pcds/pyps/config/tst/iocmanager](/reg/g/pcds/pyps/config/tst/iocmanager)).
    * Source `initIOC.hutch` from that directory.


initIOC.hutch
-------------

This script is part of the [IocManager](https://github.com/pcdshub/IocManager)
repository and can be found here: 
[/reg/g/pcds/pyps/apps/ioc/latest/initIOC.hutch](https://github.com/pcdshub/IocManager/blob/master/initIOC.hutch)

### Prerequisites
* Run as root
* Run after `initIOC`, such that:
    * Package `controls-basic-0.0.1` exists and has been configured.
    * `PYPS_ROOT`, `PSPKG_ROOT`, etc. have been set.

### Steps

1. Re-run the step to determine the hutch for the host (see `initIOC` step 2,
   above) and set `${cfg}`
2. Sets variables:
    * `BASEPORT=39050`
    * `PROCMGRD_ROOT=procmgrd`
    * `PROCMGRD_LOG_DIR=$IOC_DATA/$host/logs`
    * `IOC_USER=${cfg}ioc` (e.g., `lfeioc`, with one exception: `xrt` maps to
      `feeioc`)
    * `IOC=$(hostname -s)`
3. Set variables, if not previously set
	* `IOC_COMMON=/reg/d/iocCommon`
	* `IOC_DATA=/reg/d/iocData`
4. Source `$IOC_COMMON/All/${cfg}_env.sh`
    * This is a spot for per-hutch environment variables.
    * See, for example, [xpp_env.sh](https://github.com/pcdshub/iocCommon-All/blob/pcds-All/xpp_env.sh).
    * Many (if not all) of these per-hutch scripts will source a common
      environment script, detailed in the following section - `common_env.sh`.
5. Find the procmgrd bin directory by way of the `PROCSERV` variable (likely
   set in `common_env.sh`).
    * Set `PROCMGRD_DIR` to the bin directory
6. Create the procmgrd log directory (`$PROCMGRD_LOG_DIR`), accessible as the
   user `IOC_USER` with group write permissions.
    * Per-hutch scripts may modify `IOC_USER`, but this change will not apply
      during the directory creation process (the original is retained as
      `${cfguser}`).
7. Sets some procmgrd configuration settings
   https://github.com/pcdshub/IocManager/blob/4744dce3e9561fd6737bea4f82b00ecee0a214de/initIOC.hutch#L44-L51
    * Allows for connections from anywhere
    * Unlimited core dump size
    * Child processes start in `/tmp`
    * Readline and filename expansion are disabled.
    * In short:
        * `PROCMGRD_ARGS="--allow --ignore '^D' --coresize 0 -c /tmp"`
        * `PROCMGRD_SHELL="/bin/sh --noediting -f"`
8. Start up several process manager daemons
    * For the hutch itself (assuming not `xrt` or `las`) (as `${cfguser}`, port `BASEPORT`)
    * For the FEE (as `feeioc`, port `BASEPORT + 2`)
    * For the laser hall (as `lasioc`, port `BASEPORT + 4`)
9. Disable hyperthreading (by way of the service ` hyperthreading-disable`)
    * It's possible this service may not exist on the IOC machines.
    * It's not part of the puppet modules nor is it on e.g., `ioc-kfe-srv01`. 
10. Load the event receiver (EVR) module if it's not already loaded
    * `$IOC_ROOT/../modules/ev2_driver/latest/driver/evr_load_module`
    * Which, as `$IOC_ROOT` is set by `ioc.sh` by default (unless overridden by
      other scripts), may default to
      `/reg/g/pcds/package/epics/3.14/modules/ev2_driver/latest/driver/evr_load_module`.
    * Device: `/dev/era0` or `/dev/ega0` (MRF EVG)
11. Start the EDT driver
    * Script (hard-coded): `/opt/EDTpdv/edtinit start`
    * Device: `/dev/edt0`
12. Resets variables:
    * `IOC=$(hostname -s)`
13. Start the `caRepeater`
    * Uses script `$SCRIPTROOT/runRepeater`
      (`SCRIPTROOT=$PYPS_ROOT/config/$cfg/iocmanager`)
    * Logs to `$IOC_DATA/$IOC_HOST/iocInfo/caRepeater.log`
14. Starts all IOCs by way of `startAll` (see following section)
    * Starts those from the hutch, then xrt, then laser hall
    * Arguments are: 
        * `$1=` `${cfg}`, xrt, or las
        * `$2=$host`

common_env.sh
-------------

Source: [common_env.sh](https://github.com/pcdshub/iocCommon-All/blob/pcds-All/common_env.sh)

Sets common environment variables for launching IOCs.

### Prerequisites
* Run as root or `$IOC_USER`
* Variables set:
    * `$IOC_USER` (username)
    * `$IOC` (short hostname of IOC host, or soft IOC name)

### Steps

1. Source the first one that exists of:
	* /usr/local/lcls/epics/config/common_dirs.sh 
	* /reg/g/pcds/pyps/config/common_dirs.sh
	* /afs/slac/g/lcls/epics/config/common_dirs.sh
2. The 2nd item from step (1) is included in this repository: 
   [common_dirs.sh](/reg/g/pcds/pyps/config/common_dirs.sh)
    * The following variables of note are set:
    ```
    CONFIG_SITE_TOP=/reg/g/pcds/pyps/config
    CTRL_REPO=file:///afs/slac/g/pcds/vol2/svn/pcds
    DATA_SITE_TOP=/reg/d
    EPICS_SETUP=$SETUP_SITE_TOP
    EPICS_SITE_TOP=/reg/g/pcds/epics
    FACILITY_ROOT=/reg/g/pcds
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
    TOOLS_SITE_TOP=/reg/common/tools
    ```
3. Source `epicsenv-cur.sh` from `/reg/g/pcds/setup/epicsenv-cur`
    * Exception: on ARM7L platforms, `epicsenv-3.15.5-apalis-2.0.sh` is used.
4. Set the variables:
    * If not already set, `PROCSERV_VERSION=2.8.0-1.1.0`
    * Fix `PROCSERV_VERSION`, `CROSS_ARCH`, `PYTHON_VERSION` and path variables
      for ARM if necessary.
    * Add `$PSPKG_ROOT/release/procServ/$PROCSERV_VERSION/$EPICS_HOST_ARCH/bin`
      to `$PATH` if it exists.
    * `PROCSERV_EXE` to the absolute path of `procServ`
	* `PROCSERV="$PROCSERV_EXE --allow --ignore ^D^C --logstamp"`
    * `IOC_HOST=$(hostname -s)`
    * `CREATE_TIME` to the current date, down to the second.
5. Ensure `IOC_USER` is set - warn and exit without error if not.
6. By way of `/sbin/runuser` or `su`, perform as `$IOC_USER`:
    * Create `$IOC_DATA/$IOC_HOST`, ensure it's writable by `ps-ioc`
    * Create subdirectories `{archive,autosave,iocInfo,logs}`
7. Check `$IOC` is set or warn and exit without error.
8. As `$IOC_USER`, make `$IOC_DATA/$IOC`
    * Create subdirectories `{archive,autosave,iocInfo,logs}` with lax
      permissions (and ps-ioc accessibility)

startAll
--------

Source: [startAll.py](https://github.com/pcdshub/IocManager/blob/master/startAll.py)
(Wrapped by [startAll](https://github.com/pcdshub/IocManager/blob/master/startAll))

"startAll hutch hostname" starts all of the IOCs for the given hutch on the
given hostname.

### Prerequisites
* For the wrapper script `startAll`:
* First argument: hutch (or xrt, las) - referred to as `cfg`
* Second argument: host

### Steps

#### Wrapper

1. Set variables, if not previously set
    * `PYPS_ROOT=/reg/g/pcds/pyps`
    * `PSPKG_ROOT=/reg/g/pcds/pkg_mgr`
    * `PSPKG_RELEASE=controls-basic-0.0.1`
    * `SCRIPTROOT=/reg/g/pcds/pyps/config/$1/iocmanager` (where `$1=hutch`)
2. Run `python $SCRIPTROOT/startAll.py "$@"` (with all arguments)

#### startAll.py

* TODO

epicsenv-cur
------------

Source: [epicsenv-cur](https://github.com/pcdshub/epics-setup/blob/pcds-master/epicsenv-cur.sh)
A soft-link to the latest version. At the time of writing, this is:
[epicsenv-7.0.2-2.0.sh](https://github.com/pcdshub/epics-setup/blob/pcds-master/epicsenv-7.0.2-2.0.sh))

### Prerequisites
* None

### Steps

7.0.2-2.0 is used for example here.

1. Source common directories scripts [/reg/g/pcds/pyps/config/common_dirs.sh](/reg/g/pcds/pyps/config/common_dirs.sh).
2. Set variables 

    ```
    EPICS_SITE_TOP=/reg/g/pcds/epics
    BASE_MODULE_VERSION=R7.0.2-2.0
    EPICS_EXTENSIONS=${EPICS_SITE_TOP}/extensions/R0.2.0
    EPICS_BASE=${EPICS_SITE_TOP}/base/${BASE_MODULE_VERSION}
    EPICS_MODULES=${EPICS_SITE_TOP}/${BASE_MODULE_VERSION}/modules
    ```
3. Source some utilities for munging paths together in
   [pathmunge.sh](https://github.com/pcdshub/epics-setup/blob/pcds-master/pathmunge.sh)
4. Clear `PVACCESS`, `PVAPY` if previously set, and purges any paths associated with
   pvAccess or pvaPy from `LD_LIBRARY_PATH`, `PYTHONPATH`, and `PATH`.
5. Sources [generic-epics-setup.sh](https://github.com/pcdshub/epics-setup/blob/pcds-master/generic-epics-setup.sh)
    * See separate section below.
6. Sources [pcds_shortcuts.sh](https://github.com/pcdshub/epics-setup/blob/pcds-master/pcds_shortcuts.sh)
    * See separate section below.

generic-epics-setup.sh
----------------------

Source: [generic-epics-setup.sh](https://github.com/pcdshub/epics-setup/blob/pcds-master/generic-epics-setup.sh)

### Prerequisites
Must be set:
* `$EPICS_SITE_TOP`
* `$SETUP_SITE_TOP`
* `$TOOLS_SITE_TOP`

And then to choose a specific version:
* `$EPICS_BASE` - Path to top of base release
* `$EPICS_EXTENSIONS` - Path to top of extensions release

For versions before R7, the following are needed as well:
* `$NORMATIVETYPES`, `$PVACCESS`, `$PVDATA`, and `$PVAPY`

Setting `EPICS_CA_AUTO_ADDR_LIST` will avoid `epics-ca-env.sh` from being
sourced.

### Steps

1. Verify that the necessary variables are set
2. Set up Channel Access address list settings, if not currently configured 
    * This only checks whether `$EPICS_CA_AUTO_ADDR_LIST` is set.
    * Sources [epics-ca-env.sh](https://github.com/pcdshub/epics-setup/blob/pcds-master/epics-ca-env.sh)
3. At this point, the CA environment should be configured such that the following
   variables are set (based on `epics-ca-env.sh`):
   ```
    EPICS_CA_SERVER_PORT=5064
    EPICS_CA_REPEATER_PORT=5065
    EPICS_CA_MAX_ARRAY_BYTES=40000000
    EPICS_CA_AUTO_ADDR_LIST=YES
    EPICS_CA_BEACON_PERIOD=15.0
    EPICS_CA_CONN_TMO=30.0
    EPICS_CA_MAX_SEARCH_PERIOD=300

    # EPICS pvAccess env variables
    EPICS_PVA_SERVER_PORT=5075
    EPICS_PVA_BROADCAST_PORT=5076
    EPICS_PVA_AUTO_ADDR_LIST=YES
    ```

    Depending on the host, `EPICS_CA_ADDR_LIST` may be set as well.
4. Source some utilities for munging paths together in
   [pathmunge.sh](https://github.com/pcdshub/epics-setup/blob/pcds-master/pathmunge.sh)
5. Paths will be added to `PATH`:
    * `$TOOLS_SITE_TOP/bin` (`/reg/common/tools/bin`)
    * `$TOOLS_SITE_TOP/script` (`/reg/common/tools/script`)
6. Additional variables will be set:
    * `EPICS_HOST_ARCH=$(${EPICS_BASE}/startup/EpicsHostArch)` (e.g., `rhhel7-x86_64`)
7. Stale EPICS-related paths will be purged, including those from `PATH`,
   `LD_LIBRARY_PATH`, and `MATLABPATH`.
8. New paths will be added, as necessary to `LD_LIBRARY_PATH`:
    * `${EPICS_BASE}/lib/${EPICS_HOST_ARCH}`
    * `${EPICS_EXTENSIONS}/lib/${EPICS_HOST_ARCH}` (if set)
9. (Support for deprecated pvAccess/V4 stuff skipped)
    * One worth noting: `pvaPy` for 2.7 gets added to `$PYTHONPATH` if `$PVAPY`
      set.
10. If `$EPICS_EXTENSIONS` is set
    * Configure EDM. Set:
        * `EDMLIBS`
        * `EDMHELPFILES`
        * `EDMWEBBROWSER`
        * `EDM`
        * `EDMFILES`
	    * `EDMCALC`
	    * `EDMOBJECTS`
	    * `EDMPVOBJECTS`
	    * `EDMFILTERS`
	    * `EDMUSERLIB`
    * Configure VisualDCT. Set:
		* `VDCT_CLASSPATH="${EPICS_EXTENSIONS}/javalib/VisualDCT.jar"`

epics-ca-env.sh
---------------

### Steps

1. Sets variables
    ```
    EPICS_CA_SERVER_PORT=5064
    EPICS_CA_REPEATER_PORT=5065
    EPICS_CA_MAX_ARRAY_BYTES=40000000
    EPICS_CA_AUTO_ADDR_LIST=YES
    EPICS_CA_BEACON_PERIOD=15.0
    EPICS_CA_CONN_TMO=30.0
    EPICS_CA_MAX_SEARCH_PERIOD=300

    # EPICS pvAccess env variables
    EPICS_PVA_SERVER_PORT=5075
    EPICS_PVA_BROADCAST_PORT=5076
    EPICS_PVA_AUTO_ADDR_LIST=YES
    HOSTNAME=$(hostname)

    ARCHIVER_URL=http://pscaa02.slac.stanford.edu:17665/mgmt/ui/index.html
    ARCHIVE_VIEWER_URL=https://pswww.slac.stanford.edu/archiveviewer/retrieval/ui/viewer/archViewer.html
    ```

2. A seemingly non-existent file: `/afs/slac/g/pcds/setup/lcls-ca-env.sh` is
    referenced as well, if running on a machine without access to `/reg/neh`:
    https://github.com/pcdshub/epics-setup/blob/b37c18ce5a6771fceb0a6c6b141cc6e32318c922/epics-ca-env.sh#L20-L24

3. Depending on the host, `EPICS_CA_AUTO_ADDR_LIST` and `EPICS_CA_ADDR_LIST`
   will be set as well.

4. Adds bash aliases for viewing the archiver:
    * `Archiver`
    * `ArchiveManager`
    * `ArchiveViewer`

For the following hosts, `EPICS_CA_AUTO_ADDR_LIST` will be set to `NO`,
and the table of addresses will be set as `EPICS_CA_ADDR_LIST`.


| Host          | EPICS_CA_ADDR_LIST | EPICS_CA_AUTO_ADDR_LIST |
|---------------|--------------------|-------------------------|
| pscaasrv      | 134.79.165.255     | NO                      |
| pscaesrv      | 134.79.165.255     | NO                      |
| pscaa0*       | 134.79.165.255     | NO                      |
| tmo-control   | 172.21.135.255     | NO                      |
| tmo-monitor   | 172.21.135.255     | NO                      |
| tmo-daq       | 172.21.135.255     | NO                      |
| tmo-console   | 172.21.135.255     | NO                      |
| amo-control   | 172.21.37.255      | NO                      |
| amo-monitor   | 172.21.37.255      | NO                      |
| amo-daq       | 172.21.37.255      | NO                      |
| amo-console   | 172.21.37.255      | NO                      |
| cxi-control   | 172.21.71.255      | NO                      |
| cxi-monitor   | 172.21.71.255      | NO                      |
| cxi-daq       | 172.21.71.255      | NO                      |
| cxi-console   | 172.21.71.255      | NO                      |
| mfx-hutch01   | 172.21.75.255      | NO                      |
| mfx-control   | 172.21.75.255      | NO                      |
| mfx-monitor   | 172.21.75.255      | NO                      |
| mfx-daq       | 172.21.75.255      | NO                      |
| mfx-console   | 172.21.75.255      | NO                      |
| ioc-mec-rec01 | 172.21.79.255      | NO                      |
| mec-control   | 172.21.79.255      | NO                      |
| mec-monitor   | 172.21.79.255      | NO                      |
| mec-daq       | 172.21.79.255      | NO                      |
| mec-console   | 172.21.79.255      | NO                      |
| ioc-xcs-misc1 | 172.21.83.255      | NO                      |
| xcs-control   | 172.21.83.255      | NO                      |
| xcs-daq       | 172.21.83.255      | NO                      |
| xcs-console   | 172.21.83.255      | NO                      |
| xpp-control   | 172.21.87.255      | NO                      |
| xpp-daq2      | 172.21.87.255      | NO                      |
| xpp-daq       | 172.21.87.255      | NO                      |
| ioc-fee-rec*  | 172.21.91.255      | NO                      |
| sxr-elog      | 172.21.95.255      | NO                      |
| sxr-control   | 172.21.95.255      | NO                      |
| sxr-monitor   | 172.21.95.255      | NO                      |
| sxr-daq       | 172.21.95.255      | NO                      |
| sxr-console   | 172.21.95.255      | NO                      |


pcds_shortcuts.sh
-----------------

Source: [pcds_shortcuts.sh](https://github.com/pcdshub/epics-setup/blob/pcds-master/pcds_shortcuts.sh)

### Steps
1. If not previously set, sets:
    ```
    CONFIG_SITE_TOP=/reg/g/pcds/pyps/config
    PACKAGE_SITE_TOP=/reg/g/pcds/package
    EPICS_SITE_TOP=/reg/g/pcds/epics
    IOC_COMMON=/reg/d/iocCommon
    IOC_DATA=/reg/d/iocData
    PYPS_SITE_TOP=/reg/g/pcds/pyps
    PKGS=$PACKAGE_SITE_TOP
    ```

2. Sets `umask 0002`, allowing group write access to files written.
   This results in `umask -S`: `u=rwx,g=rwx,o=rx`
3. Adds many utility (bash) functions to the environment (see table)
4. Sets:
    * `$IP` to the current machine's IP address.
    * `$MASK` to the subnet mask (appears to be buggy)
    * `$SUBNET` to the third octet of `$IP` (fixing for /22 subnet masks as well)
    * These variables can be used to determine where screens are being launched
      from, for example.

#### Non-screen functions

| Function            | Description                                                                              | Script                                                     |
|---------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------|
| find_pv             | This script will search for each specified EPICS PV in pvlist files and startup scripts. |                                                            |
| gsed                | Wrapper for `sed`, operating on multiple files in-place and noting which changed.        |                                                            |
| show_epics_sioc     | Similar to `ssh_show_procServ`, this shows a table of IOCs - but on one or more hosts.   |                                                            |
| show_epics_versions | An alias for the `epics-versions` tool.                                                  |                                                            |
| ssh_show_procServ   | Shows a table of procServ information including port numbers.                            |                                                            |
| svnvdiff            | (Alias) Run a visual diff tool for ye old SVN.                                           | svn diff --diff-cmd $TOOLS_SITE_TOP/bin/svn-vdiffwrap.sh   |

#### Screen helpers

| Function            | Description                                                            | Script                                                     |
|---------------------|------------------------------------------------------------------------|------------------------------------------------------------|
| cxi                 | CXI screen.                                                            | /reg/g/pcds/epics-dev/screens/edm/cxi/current/cxihome      |
| det                 | Top-level detector screen.                                             | /reg/g/pcds/epics-dev/screens/edm/det/current/detHome.sh   |
| fee                 | Deprecated - no longer launches the FEE screen. (aliases: xrt, xtod)   | Was: /reg/g/pcds/epics-dev/screens/edm/fee/current/feehome |
| gw                  | Gateway screen.                                                        | /reg/g/pcds/epics-dev/screens/edm/gateway/current/gwhome   |
| hpl                 | HPL screen.                                                            | /reg/g/pcds/epics-dev/screens/edm/hpl/current/hplhome      |
| kfe                 | LUCID KFE screen.                                                      | ${EPICS_SETUP}/lucid-launcher.sh KFE                       |
| kpmps               | KFE PMPS screen.                                                       | ${EPICS_SETUP}/pmps-launcher.sh KFE                        |
| las                 | Laser screen.                                                          | /reg/g/pcds/epics-dev/screens/edm/las/current/laserhome    |
| lfe                 | LUCID LFE screen.                                                      | ${EPICS_SETUP}/lucid-launcher.sh LFE                       |
| lpmps               | LFE PMPS screen.                                                       | ${EPICS_SETUP}/pmps-launcher.sh LFE                        |
| mec                 | MEC screen.                                                            | /reg/g/pcds/epics-dev/screens/edm/mec/current/mechome      |
| mfx                 | MFX screen.                                                            | /reg/g/pcds/epics-dev/screens/edm/mfx/current/mfxhome      |
| pcds                | Top-level PCDS screen.                                                 | /reg/g/pcds/epics-dev/screens/edm/pcds/current/pcdshome    |
| pydm_lclshome       | Top-level PyDM screen.                                                 | ${EPICS_SETUP}/pydm_lclshome.sh                            |
| tmo                 | LUCID TMO screen.                                                      | ${EPICS_SETUP}/lucid-launcher.sh TMO                       |
| tst                 | TST screen.                                                            | /reg/g/pcds/epics-dev/screens/edm/tst/current/tsthome      |
| updateScreenLinks   | Update screen links for given hutches.                                 |                                                            |
| xcs                 | XCS screen.                                                            | /reg/g/pcds/epics-dev/screens/edm/xcs/current/xcshome      |
| xpp                 | XPP screen.                                                            | /reg/g/pcds/epics-dev/screens/edm/xpp/current/xpphome      |

### ssh_show_procServ

Usage: `ssh_show_procServ [host] [user]`

`host` defaults to the current machine, and `user` defaults to `$USER`.

Shows a table of procServ information including port numbers:

```bash
[klauer@ioc-kfe-srv01  setup]$ ssh_show_procServ
2943   kfeioc    caRepeater                procServ  ioc-kfe-srv01       30000
3150   kfeioc    ioc-plc-kfe-gatt          procServ  ioc-kfe-srv01       31313
3152   kfeioc    ioc-kfe-gmd-vac           procServ  ioc-kfe-srv01       30105
3154   kfeioc    ioc-kfe-gmd-vac-support   procServ  ioc-kfe-srv01       30102
3241   kfeioc    ioc-kfe-mono-gige03       procServ  ioc-kfe-srv01       34203
3471   kfeioc    ioc-kfe-mono-gige04       procServ  ioc-kfe-srv01       34204
3627   kfeioc    ioc-kfe-motion            procServ  ioc-kfe-srv01       34242
3735   kfeioc    ioc-kfe-rix-motion        procServ  ioc-kfe-srv01       34222
3836   kfeioc    ioc-kfe-rtd01             procServ  ioc-kfe-srv01       30150
4003   kfeioc    ioc-kfe-twistorr-debug    procServ  ioc-kfe-srv01       30110
4084   kfeioc    ioc-kfe-vac               procServ  ioc-kfe-srv01       30104
4375   kfeioc    ioc-kfe-vac-support       procServ  ioc-kfe-srv01       30100
4535   kfeioc    ioc-kfe-xgmd-vac          procServ  ioc-kfe-srv01       30106
4884   kfeioc    ioc-kfe-xgmd-vac-support  procServ  ioc-kfe-srv01       30101
5031   kfeioc    ioc-mcp-tmo-al1k4         procServ  ioc-kfe-srv01       30250
5188   kfeioc    ioc-rixs-optics           procServ  ioc-kfe-srv01       30107
5513   kfeioc    ioc-tmo-optics            procServ  ioc-kfe-srv01       30103
```

### show_epics_sioc

Usage: `show_epics_sioc [host1] [host2...]`
Usage: `show_epics_sioc all`

Similar to `ssh_show_procServ`, this shows a table of IOCs - but on one or more
hosts (or even _all_ configured hosts, found from `$IOC_COMMON/hosts`).

```bash
[klauer@ioc-kfe-srv01  setup]$ show_epics_sioc ioc-lfe-srv01
PID    USER      SIOC                      COMMAND   HOSTNAME            PORT
2956   lfeioc    caRepeater                procServ  ioc-lfe-srv01       30000
3163   lfeioc    ioc-lfe-at1l0             procServ  ioc-lfe-srv01       31113
3165   lfeioc    ioc-lfe-gatt-serial       procServ  ioc-lfe-srv01       31013
3167   lfeioc    ioc-plc-lfe-gem           procServ  ioc-lfe-srv01       31313
3170   lfeioc    ioc-lfe-motion            procServ  ioc-lfe-srv01       34242
3359   lfeioc    ioc-lfe-optics            procServ  ioc-lfe-srv01       30014
3654   lfeioc    ioc-lfe-plv-psu           procServ  ioc-lfe-srv01       30301
3776   lfeioc    ioc-lfe-pwr-01            procServ  ioc-lfe-srv01       30001
4012   lfeioc    ioc-lfe-pwr-02            procServ  ioc-lfe-srv01       30002
4225   lfeioc    ioc-lfe-rtd01             procServ  ioc-lfe-srv01       30131
4420   lfeioc    ioc-lfe-vac               procServ  ioc-lfe-srv01       30111
4574   lfeioc    ioc-lfe-vac-support       procServ  ioc-lfe-srv01       30100
4778   lfeioc    ioc-txi-optics            procServ  ioc-lfe-srv01       30015
```


### find_pv

Usage: find_pv pv_name [pv_name2 ...]

This script will search for each specified EPICS PV in:
  /reg/d/iocData/ioc*/iocInfo/IOC.pvlist

Then it looks for the linux host or hard IOC hostname in:
  /reg/d/iocCommon/hioc/ioc*/startup.cmd
If no host is found, the IOC will not autoboot after a power cycle!

Finally it looks for the boot directory in:
  /reg/d/iocCommon/hioc/<ioc-name>/startup.cmd

Hard IOC boot directories are shown with the nfs mount name.
Typically this is /iocs mounting /reg/g/pcds/package/epics/ioc


### updateScreenLinks

usage: `updateScreenLinks <pathToScreenRelease>`

Creates a soft link to the specified directory in the epics-dev version of each
hutch's edm home directory.  The soft link name is derived from the basename of
the provided path.

If an absolute path is not provided, the path is evaluated relative to the root
of our EPICS releases:

    /reg/g/pcds/epics

Examples:

```
updateScreenLinks /reg/g/pcds/epics/ioc/las/fstiming/R2.3.0/fstimingScreens
updateScreenLinks modules/history/R0.4.0/historyScreens
```


### gsed

```
Usage: gsed sedExpr file ....
Example: gsed s/R0.1.0/R0.2.0/g ioc-tst-cam1.cfg ioc-*2.cfg

$ sed s/R0.1.0/R0.2.0/g in specified files
============ ioc-tst-cam1.cfg: UPDATED
============ ioc-tst-cam2.cfg: Same, N/C
```
