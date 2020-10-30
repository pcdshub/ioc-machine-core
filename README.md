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

common_env.sh
-------------

[common_env.sh](https://github.com/pcdshub/iocCommon-All/blob/pcds-All/common_env.sh)

startAll
--------

[startAll](https://github.com/pcdshub/IocManager/blob/master/startAll)
