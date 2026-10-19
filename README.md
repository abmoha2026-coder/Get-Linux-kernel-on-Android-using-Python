# Get-Linux-kernel-on-Android-using-Python

A small Python package for fetching, building, installing, and interacting with Linux kernels on Android devices.

Installation

    python3 -m pip install .

Quick usage

    kernel-android-tool fetch https://github.com/torvalds/linux.git linux-src --depth 1
    kernel-android-tool build linux-src --arch arm64 --cross aarch64-linux-gnu- --target Image
    kernel-android-tool install-modules linux-src /tmp/kernel-modules --arch arm64 --cross aarch64-linux-gnu-
    kernel-android-tool devices
    kernel-android-tool shell "uname -a"
    kernel-android-tool env-check

Commands

- fetch: clone a Linux kernel source repository
- build: run make for the selected architecture and target
- install-modules: install built kernel modules into a local tree
- push-modules: copy .ko files to /system/lib/modules on a connected Android device
- devices: list connected adb devices
- shell: execute a command in the Android shell
- flash-boot: flash a boot image with fastboot
- env-check: confirm that required host tools are installed

Notes

- Building kernels for Android often requires a cross compiler and correct ARCH/CROSS_COMPILE values.
- Flashing boot images or modifying system modules is device- and vendor-specific and may require root or an unlocked bootloader.
- This is intended for research, development, and experimentation; use it carefully.
