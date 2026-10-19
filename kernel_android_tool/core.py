import os
import shutil
import subprocess
from pathlib import Path


def run(cmd, cwd=None, env=None, check=True):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, env=env, check=check)


def check_tool(name):
    return shutil.which(name)


def fetch_kernel(git_url, dest, branch=None, depth=1):
    dest_path = Path(dest)
    if dest_path.exists() and any(dest_path.iterdir()):
        raise SystemExit(f"Destination {dest} already exists and is not empty")

    cmd = ["git", "clone", git_url, str(dest_path)]
    if branch:
        cmd = ["git", "clone", "--branch", branch, git_url, str(dest_path)]
    if depth and depth > 0:
        if branch:
            cmd = ["git", "clone", "--branch", branch, "--depth", str(depth), git_url, str(dest_path)]
        else:
            cmd = ["git", "clone", "--depth", str(depth), git_url, str(dest_path)]

    run(cmd)
    print("Kernel source fetched successfully.")


def build_kernel(src_dir, arch=None, cross_compile=None, jobs=None, target="Image"):
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

    if jobs is None:
        jobs = os.cpu_count() or 4

    cmd = [make, f"-j{jobs}", target]
    run(cmd, cwd=str(src), env=env)
    print(f"Kernel build finished. Check output for {target}.")


def install_modules(src_dir, install_path, arch=None, cross_compile=None):
    src = Path(src_dir)
    install_root = Path(install_path)
    install_root.mkdir(parents=True, exist_ok=True)

    make = shutil.which("make") or shutil.which("gmake")
    if not make:
        raise SystemExit("make not found in PATH")

    env = os.environ.copy()
    if arch:
        env["ARCH"] = arch
    if cross_compile:
        env["CROSS_COMPILE"] = cross_compile

    cmd = [make, f"INSTALL_MOD_PATH={install_root}", "modules_install"]
    run(cmd, cwd=str(src), env=env)
    print(f"Kernel modules installed to {install_root}")


def adb(args):
    adb_bin = shutil.which("adb")
    if not adb_bin:
        raise SystemExit("adb not found in PATH")
    run([adb_bin, *args])


def fastboot(args):
    fb = shutil.which("fastboot")
    if not fb:
        raise SystemExit("fastboot not found in PATH")
    run([fb, *args])


def list_devices():
    adb(["devices"])


def device_shell(command):
    adb(["shell", command])


def push_file(local, remote):
    adb(["push", local, remote])


def push_modules_to_device(local_modules_path, device_modules_path="/system/lib/modules", remount=True):
    local = Path(local_modules_path)
    if not local.exists():
        raise SystemExit(f"Local modules path {local} does not exist")

    if remount:
        try:
            adb(["root"])
        except Exception:
            print("adb root failed; device may not allow adb root.")
        try:
            adb(["remount"])
        except Exception:
            print("adb remount failed; device may not allow it.")

    for kernel_obj in local.rglob("*.ko"):
        rel = kernel_obj.relative_to(local)
        remote_path = f"{device_modules_path}/{rel}"
        remote_dir = str(Path(remote_path).parent)
        adb(["shell", "mkdir", "-p", remote_dir])
        push_file(str(kernel_obj), remote_path)

    print("Module push complete.")


def flash_boot_image(boot_img_path, require_confirm=True):
    if require_confirm:
        answer = input(f"Flash {boot_img_path} with fastboot? Type 'yes' to continue: ")
        if answer.strip().lower() != "yes":
            print("Aborted flash.")
            return
    fastboot(["flash", "boot", boot_img_path])
    fastboot(["reboot"])


def check_environment():
    tools = ["git", "make", "adb", "fastboot"]
    print("Environment check:")
    for tool in tools:
        print(f"  {tool}: {'OK' if check_tool(tool) else 'MISSING'}")

