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

Expectations:
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
6. Finally, launch IocManager by way of [/reg/g/pcds/pyps/apps/ioc/latest/initIOC](/reg/g/pcds/pyps/apps/ioc/latest/initIOC)
