#!/usr/bin/env python3
"""
kernel_tool.py

A simple Python-based CLI to fetch/build/install and interact with Linux kernels
for Android devices. This tool wraps git/make/adb/fastboot calls and provides
convenience commands — it does NOT automate unlocking bootloaders or bypassing
safety checks. Use with caution.

Requirements: git, make, cross-compiler toolchain (if building for Android arch),
adb, fastboot. Python 3.8+

"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd, cwd=None, env=None, check=True):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, env=env, check=check)


def check_tool(name):
    path = shutil.which(name)
    if path is None:
        print(f"WARNING: {name} not found in PATH")
    return path


def fetch_kernel(git_url, dest, branch=None, depth=1):
    dest_path = Path(dest)
    if dest_path.exists() and any(dest_path.iterdir()):
        raise SystemExit(f"Destination {dest} already exists and is not empty")
    cmd = ["git", "clone", git_url, dest]
    if branch:
        cmd = ["git", "clone", "--branch", branch, git_url, dest]
    if depth and depth > 0:
        # shallow clone
        if branch:
            cmd = ["git", "clone", "--branch", branch, "--depth", str(depth), git_url, dest]
        else:
            cmd = ["git", "clone", "--depth", str(depth), git_url, dest]
    run(cmd)
    print("Clone complete")


def build_kernel(src_dir, arch=None, cross_compile=None, jobs=None, target="Image or zImage or modules"):
    src = Path(src_dir)
    if not src.exists():
        raise SystemExit(f"Source directory {src_dir} does not exist")
    make = shutil.which("make") or shutil.which("gmake")
    if not make:
        raise SystemExit("make not found in PATH")
    env = os.environ.copy()
    if arch:
        env["ARCH"] = arch
    if cross_compile:
        env["CROSS_COMPILE"] = cross_compile
    if not jobs:
        try:
            jobs = str(os.cpu_count() or 4)
        except Exception:
            jobs = "4"
    cmd = [make, f"-j{jobs}"]
    # default build target
    cmd.append("bzImage")
    print("Building kernel — this can take a long time. Pass a correct ARCH/CROSS_COMPILE if needed.")
    run(cmd, cwd=str(src), env=env)
    print("Build finished — check the arch-specific Image/zImage in the build output")


def install_modules(src_dir, install_path, arch=None, cross_compile=None):
    src = Path(src_dir)
    if not src.exists():
        raise SystemExit(f"Source directory {src_dir} does not exist")
    install_path = Path(install_path)
    install_path.mkdir(parents=True, exist_ok=True)
    make = shutil.which("make") or shutil.which("gmake")
    if not make:
        raise SystemExit("make not found in PATH")
    env = os.environ.copy()
    if arch:
        env["ARCH"] = arch
    if cross_compile:
        env["CROSS_COMPILE"] = cross_compile
    cmd = [make, f"INSTALL_MOD_PATH={str(install_path)}", "modules_install"]
    run(cmd, cwd=str(src), env=env)
    print(f"Modules installed to {install_path}")


def adb(cmd_args):
    adb_bin = shutil.which("adb")
    if not adb_bin:
        raise SystemExit("adb not found in PATH")
    cmd = [adb_bin] + cmd_args
    run(cmd)


def fastboot(cmd_args):
    fb = shutil.which("fastboot")
    if not fb:
        raise SystemExit("fastboot not found in PATH")
    cmd = [fb] + cmd_args
    run(cmd)


def list_devices():
    adb(["devices"])


def device_shell(cmd):
    adb(["shell", cmd])


def push_file(local, remote):
    adb(["push", local, remote])


def push_modules_to_device(local_modules_path, device_modules_path="/system/lib/modules", remount=True):
    # Requires a rooted device or system writable
    adb_bin = shutil.which("adb")
    if not adb_bin:
        raise SystemExit("adb not found in PATH")
    local = Path(local_modules_path)
    if not local.exists():
        raise SystemExit(f"Local modules path {local} does not exist")
    if remount:
        try:
            adb(["root"])
        except Exception:
            print("adb root failed — device might not allow root via adb")
        adb(["remount"])
    # push whole tree
    for p in local.rglob("*.ko"):
        rel = p.relative_to(local)
        remote = f"{device_modules_path}/{rel}"
        # create remote directory
        remote_dir = os.path.dirname(remote)
        adb(["shell", "mkdir", "-p", f"{remote_dir}"])
        push_file(str(p), remote)
    print("Module push complete. You may need to depmod/insmod on the device.")


def flash_boot_image(boot_img_path, require_confirm=True):
    if require_confirm:
        ans = input(f"About to flash {boot_img_path} to the device boot partition via fastboot. Type 'yes' to continue: ")
        if ans.strip().lower() != "yes":
            print("Aborted flash")
            return
    fastboot(["flash", "boot", boot_img_path])
    fastboot(["reboot"])


def check_environment():
    tools = ["git", "make", "adb", "fastboot"]
    found = {}
    for t in tools:
        found[t] = shutil.which(t) is not None
    print("Environment check:")
    for t, ok in found.items():
        print(f"  {t}: {'OK' if ok else 'MISSING'}")


def main():
    parser = argparse.ArgumentParser(description="Kernel tool: fetch, build, install and interact with kernels for Android")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("fetch", help="Clone kernel source from git")
    p.add_argument("url")
    p.add_argument("dest")
    p.add_argument("--branch", default=None)
    p.add_argument("--depth", type=int, default=1)

    p = sub.add_parser("build", help="Build the kernel")
    p.add_argument("src")
    p.add_argument("--arch", default=os.environ.get("ARCH"))
    p.add_argument("--cross", default=os.environ.get("CROSS_COMPILE"))
    p.add_argument("--jobs", type=int, default=os.cpu_count())

    p = sub.add_parser("install-modules", help="Install built modules to a local tree")
    p.add_argument("src")
    p.add_argument("dest")
    p.add_argument("--arch", default=os.environ.get("ARCH"))
    p.add_argument("--cross", default=os.environ.get("CROSS_COMPILE"))

    p = sub.add_parser("push-modules", help="Push modules from a local tree to the device")
    p.add_argument("local")
    p.add_argument("--device-path", default="/system/lib/modules")
    p.add_argument("--no-remount", dest="remount", action="store_false")

    p = sub.add_parser("devices", help="List adb devices")

    p = sub.add_parser("device-shell", help="Run a shell command on device")
    p.add_argument("command")

    p = sub.add_parser("flash-boot", help="Flash a boot image using fastboot")
    p.add_argument("bootimg")
    p.add_argument("--yes", dest="yes", action="store_true", help="Skip confirmation")

    p = sub.add_parser("env-check", help="Check required tools are present")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    try:
        if args.cmd == "fetch":
            fetch_kernel(args.url, args.dest, branch=args.branch, depth=args.depth)
        elif args.cmd == "build":
            build_kernel(args.src, arch=args.arch, cross_compile=args.cross, jobs=args.jobs)
        elif args.cmd == "install-modules":
            install_modules(args.src, args.dest, arch=args.arch, cross_compile=args.cross)
        elif args.cmd == "push-modules":
            push_modules_to_device(args.local, device_modules_path=args.device_path, remount=args.remount)
        elif args.cmd == "devices":
            list_devices()
        elif args.cmd == "device-shell":
            device_shell(args.command)
        elif args.cmd == "flash-boot":
            flash_boot_image(args.bootimg, require_confirm=not args.yes)
        elif args.cmd == "env-check":
            check_environment()
        else:
            raise SystemExit("Unknown command")
    except subprocess.CalledProcessError as e:
        print("Command failed:", e)
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
