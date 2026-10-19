# Get-Linux-kernel-on-Android-using-Python

This repository contains a small Python CLI tool to help fetch, build, and interact with Linux kernels on Android devices.

WARNING: Building and flashing kernels is device-specific and can brick your device. Use this tool only if you know what you're doing. Always have backups and an unlocked bootloader (if required) and know how to restore your device.

What this tool provides

- fetch: clone a kernel tree from git
- build: invoke make to build the kernel (requires toolchain / CROSS_COMPILE for non-host builds)
- install-modules: run "make modules_install" into a local install path
- push-modules: push .ko files to a connected Android device via adb
- devices: list adb devices
- device-shell: run a command on the device
- flash-boot: flash a boot image via fastboot (requires user confirmation)
- env-check: check presence of git/make/adb/fastboot

Prerequisites

- Python 3.8+
- git
- make
- adb and fastboot (Android Platform Tools)
- cross-compiler toolchain if building for arm/arm64 (set CROSS_COMPILE and ARCH env vars or pass via CLI)

Examples

Clone a kernel tree:

    python3 kernel_tool.py fetch https://github.com/torvalds/linux.git linux-src --depth 1

Build (example for arm64 with an aarch64 toolchain prefix):

    export CROSS_COMPILE=aarch64-linux-gnu-
    export ARCH=arm64
    python3 kernel_tool.py build linux-src --jobs 8

Install modules to a local tree:

    python3 kernel_tool.py install-modules linux-src /tmp/kernel-mods

Push modules to device (requires root and writable filesystem):

    python3 kernel_tool.py push-modules /tmp/kernel-mods --device-path /system/lib/modules

Flash a boot image (fastboot) — this will prompt for confirmation by default:

    python3 kernel_tool.py flash-boot path/to/boot.img

Notes and safety

- This tool intentionally does not attempt to automatically detect and install cross-toolchains.
- Flashing boot images and remounting system partitions require an unlocked bootloader and/or root access. The tool will not bypass device security.
- Some commands will fail on stock, non-rooted devices.

Contributions

This is a starting point. Contributions welcome: add support for building with defconfig, packing boot images (mkbootimg), integrating with Android-specific device trees, automation for vendor kernels, and safer device detection.
