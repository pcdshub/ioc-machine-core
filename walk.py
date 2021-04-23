#!/usr/bin/env python3
"""
Tool to walk scripts from ioc.service to startup, recording variables and
dependencies.

This is not a "smart" tool in that it can't figure out control flow of your
bash scripts.  If your scripts do anything beyond the basics, there is
a chance this won't pick it up.  It will make a best-effort attempt to
pick out newly-defined variables and propagate them through.

Writes a graphviz digraph, if installed.

May be run on non-PCDS machines with ``ioc_machine_core`` checked out, but
results may vary significantly if the files aren't included in this repo.
"""
import argparse
import collections
import os
import pathlib
import pprint
import re
import string
import sys
import textwrap

try:
    import graphviz
except ImportError:
    graphviz = None


FILE_RE = re.compile(r"([^ =\"':<>][/a-z_\-0-9$(){}\.]+)", re.IGNORECASE)
EXPORT_RE = re.compile(r"^export\s*([^=\n\r]+)\s*=\s*([^\n]*)$", re.MULTILINE)
NON_EXPORT_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z_0-9]+)\s*=([^\n]*)$", re.IGNORECASE | re.MULTILINE
)

MODULE_PATH = pathlib.Path(__file__).resolve().parent
if pathlib.Path("/reg/g").exists():
    # PCDS machines
    TOP_PATH = pathlib.Path("/")
else:
    # Used in isolation
    TOP_PATH = MODULE_PATH


def build_arg_parser():
    """Build the arg parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--hutch", type=str, default="ued")
    parser.add_argument("--ioc_host", type=str, default="ioc-ued-ccd01")
    parser.add_argument("--host_arch", type=str, default="rhel7-x86_64")
    parser.add_argument(
        "--starting_script", type=str, default="usr/lib/systemd/scripts/ioc.sh"
    )
    return parser


def get_basic_config(hutch, ioc_host, host_arch="rhel7-x86_64"):
    basic_config = f"""
IOC_HOST={ioc_host}
THISHOST={ioc_host}
host={ioc_host}
cfg={hutch}
T_A={host_arch}
EPICS_HOST_ARCH={host_arch}

hutch={hutch}
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
        if basic_line:
            key, value = basic_line.split("=")
            if value.startswith("/"):
                value = str(TOP_PATH) + value[1:]
            yield key, value


class TemplateState:
    def __init__(self, hutch, ioc_host, host_arch, starting_script):
        self.hutch = hutch
        self.ioc_host = ioc_host
        self.host_arch = host_arch
        self.starting_script = starting_script
        self.missing_keys = collections.defaultdict(set)
        self.missing_files = collections.defaultdict(set)
        self.bad_items = collections.defaultdict(set)
        self.ignored_bad_items = {
            prefix + str(idx) + suffix
            for prefix, suffix in [("${", "}"), ("$", ""), ("${", ""), ("($", "")]
            for idx in range(20)
        }
        self.variables = collections.defaultdict(list)
        self.special_case_expansions = {
            "$(${EPICS_BASE}/startup/EpicsHostArch)": host_arch,
            "$(${EPICS_BASE}/startup/EpicsHostArch.pl)": host_arch,
        }
        self.template_variables = dict(
            get_basic_config(
                hutch=hutch,
                ioc_host=ioc_host,
                host_arch=host_arch,
            )
        )

    def expand_text(self, reference, text, allow_missing=False):
        """Expand `text` with the current `template_variables`."""
        if text in self.special_case_expansions:
            return self.special_case_expansions[text]

        try:
            return string.Template(text).substitute(self.template_variables)
        except KeyError as ex:
            key = str(ex).strip("'")
            self.missing_keys[key].add(reference)
            if not allow_missing:
                raise
            return text

    def fix_filename(self, reference, fn):
        """
        Fix the given filename, expanding macros as necessary.

        Returns ``None`` if the file should be skipped.
        """
        fn = fn.strip("` \t\n\r|")
        if fn.startswith("//"):
            fn = "/" + fn.lstrip("/")

        try:
            fn = self.expand_text(reference, fn)
        except ValueError as ex:
            if fn not in self.ignored_bad_items:
                self.bad_items[reference].add((fn, str(ex)))
            return
        except KeyError as ex:
            return

        # More awful fix-ups:
        fn = fn.strip("()")

        if fn.startswith("/"):
            fn = str(TOP_PATH / fn[1:])

        if fn.startswith("//"):
            fn = "/" + fn.lstrip("/")

        if not fn:
            ...
        elif fn.startswith("/dev/"):
            ...
        elif fn.startswith("s/"):
            ...
        elif fn.startswith("*/"):
            ...
        elif fn.startswith("!"):
            ...
        elif "/" in fn:
            return fn


def main(hutch, ioc_host, host_arch, starting_script):
    templ = TemplateState(hutch, ioc_host, host_arch, starting_script)
    stack = [
        ("START", templ.fix_filename("START", starting_script)),
        # ("START", "/reg/d/iocCommon/All/ued_env.sh"),
    ]

    graph = graphviz.Digraph() if graphviz is not None else None
    links = {"START": {}}
    checked = set()

    while stack:
        reference, fn = stack.pop()
        if fn in checked:
            continue
        checked.add(fn)

        try:
            with open(fn, "rt") as fp:
                contents = fp.read()
        except (UnicodeDecodeError, ValueError):
            continue
        except IsADirectoryError:
            continue
        except FileNotFoundError:
            if "/" in fn and len(fn) > 5:
                templ.missing_files[fn].add(reference)
            continue

        links[fn] = {}
        links[reference][fn] = links[fn]
        if graph is not None:
            graph.node(fn)
            graph.edge(reference, fn)

        print(f"## {fn}")
        print(textwrap.indent(contents, "    > ", lambda line: True))
        for variable, value in EXPORT_RE.findall(contents):
            print(f"Found export definition: {variable}={value}", file=sys.stderr)
            templ.variables[variable].append((fn, value))
            if variable not in templ.template_variables:
                try:
                    templ.template_variables[variable] = templ.expand_text(
                        fn, value, allow_missing=True
                    ).strip()
                except ValueError:
                    templ.template_variables[variable] = value.strip()

        for variable, value in NON_EXPORT_RE.findall(contents):
            print(f"Found non-export definition: {variable}={value}", file=sys.stderr)
            templ.variables[variable].append((fn, value))

        for item in FILE_RE.findall(contents):
            item = templ.fix_filename(fn, item)
            if item:
                stack.append((fn, item))

    for key, used_in in sorted(templ.missing_keys.items()):
        print(f"! Missing key {key} used in {used_in}", file=sys.stderr)

    for fn, items in sorted(templ.bad_items.items()):
        for item, error in items:
            print(f"! In {fn}, unable to evaluate {item!r}: {error}", file=sys.stderr)

    for missing_fn, referred_by in sorted(templ.missing_files.items()):
        for referred_by in sorted(referred_by):
            print(f"! In {referred_by}, missing file {missing_fn!r}", file=sys.stderr)

    for variable, defined_locations in sorted(templ.variables.items()):
        for fn, value in defined_locations:
            print(f"In {fn}, {variable}={value}")

    if graph is not None:
        graph.render("links", format="pdf")
    return templ, links


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()
    main(
        hutch=args.hutch,
        ioc_host=args.ioc_host,
        host_arch=args.host_arch,
        starting_script=args.starting_script,
    )
