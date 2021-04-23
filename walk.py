import os
import re
import graphviz
import string
import pathlib

FILE_RE = re.compile(r"([^ =][/a-z_\-0-9$(){}\.]+)", re.IGNORECASE)

MODULE_PATH = pathlib.Path(__file__).resolve().parent
TOP_PATH = MODULE_PATH
# TOP_PATH = pathlib.Path("/")

hutch = "kfe"
ioc_host = "ioc-kfe-mot-01"
host_arch = "rhel7-x86_64"

defines = {
    "IOC_HOST": ioc_host,
    "THISHOST": ioc_host,
    "hutch": hutch,
    "host": "",
    "cfg": hutch,
    "T_A": host_arch,
}

basic_config = f"""
CONFIG_SITE_TOP=/reg/g/pcds/pyps/config
CTRL_REPO=file:///afs/slac/g/pcds/vol2/svn/pcds
DATA_SITE_TOP=/reg/d
EPICS_SETUP=/reg/g/pcds/setup
EPICS_SITE_TOP=/reg/g/pcds/epics
FACILITY_ROOT=/reg/g/pcds
GIT_SITE_TOP=/afs/slac/g/cd/swe/git/repos
GIT_TOP=/afs/slac/g/cd/swe/git/repos
GW_SITE_TOP=/reg/g/pcds/gateway
IOC_COMMON=/reg/d/iocCommon
IOC_DATA=/reg/d/iocData
PACKAGE_SITE_TOP=/reg/g/pcds/package
PSPKG_ROOT=/reg/g/pcds/pkg_mgr
PYAPPS_SITE_TOP=/reg/g/pcds/controls
PYPS_ROOT=/reg/g/pcds/pyps/
PYPS_SITE_TOP=/reg/g/pcds/pyps
SCRIPTROOT=/reg/g/pcds/pyps/config/{hutch}/iocmanager
SETUP_SITE_TOP=/reg/g/pcds/setup
TOOLS_SITE_TOP=/reg/common/tools
""".strip()

for basic_line in basic_config.splitlines():
    key, value = basic_line.split('=')
    if value.startswith("/"):
        value = str(TOP_PATH) + value
    defines[key] = str(value)

checked = set()
stack = [
    ("START", "usr/lib/systemd/scripts/ioc.sh"),
]

links = {"START": {}}
missing_keys = set()
missing_files = set()
bad_items = set()

graph = graphviz.Digraph()

while stack:
    parent_fn, fn = stack.pop()
    if fn in checked:
        continue
    checked.add(fn)
    # print(f"Saw: {fn}")

    if fn.startswith("/"):
        fn = TOP_PATH / fn[1:]

    try:
        fn = string.Template(str(fn)).substitute(defines)
    except ValueError as ex:
        bad_items.add((fn, str(ex)))
        continue
    except KeyError as ex:
        print("Missing key", ex)
        missing_keys.add(str(ex).strip("'"))
        continue

    try:
        with open(fn, "rt") as fp:
            contents = fp.read()
    except IsADirectoryError:
        continue
    except FileNotFoundError:
        if '/' in fn:
            missing_files.add(fn)
        continue

    links[fn] = {}
    links[parent_fn][fn] = links[fn]
    graph.node(fn)
    graph.edge(parent_fn, fn)

    print(f"<-- {fn} -->")
    for item in FILE_RE.findall(contents):
        item = item.strip()
        if not item:
            ...
        elif item.startswith("s/"):
            ...
        elif item.startswith("*/"):
            ...
        elif item.startswith("!"):
            ...
        elif "/" in item:
            stack.append((fn, item))


print("Missing keys", list(sorted(missing_keys)))
print("Bad items", list(sorted(bad_items)))
print("Missing files:")
for fn in sorted(missing_files):
    print(f"    {fn}")

import pprint
pprint.pprint(links)

graph.render("links", format="pdf")
