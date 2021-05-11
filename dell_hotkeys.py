#!/usr/bin/env python3
'''
script to test Dell hotkey functionality

Copyright (C) 2021 Canonical Ltd.

Authors
  Alex Hung <alex.hung@canonical.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3,
as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

The purpose of this script is to simply interact with an onboard
accelerometer, and check to be sure that the x, y, z axis respond
to physical movement of hardware.
'''
import sys, os, argparse, time, evdev, subprocess, re
from argparse import ArgumentParser
from evdev import UInput, ecodes as e
from subprocess import STDOUT, check_call, CalledProcessError

class Acpidbg(object):
    def __init__(self, method):
        self.method = method
        # install acpidbg if it is not yet installed
        kernel_ver = os.uname().release
        dir = "/usr/lib/linux-tools/" + kernel_ver +"/acpidbg"
        if not os.path.exists(dir):
            try:
                check_call(['apt', 'install', '-y','linux-tools-generic',
                    'linux-tools-' + kernel_ver], stdout=open(os.devnull, 'wb'))
            except CalledProcessError as e:
                print(e.output)

    def run_command(self, command = ''):
        command = 'e ' + self.method + ' ' + command
        try:
            check_call(['acpidbg', '-b', command], stdout=open(os.devnull, 'wb'))
        except CalledProcessError as e:
            print(e.output)
        time.sleep(1)

class Wireless(object):
    def __init__(self, name):
        self.name = name

    def get_state(self):
        rfkill_cmd = 'rfkill list ' + self.name
        out = subprocess.Popen(rfkill_cmd, shell=True, stdout=subprocess.PIPE)
        (stdout, stderr) = out.communicate()

        if stdout.decode().strip().find('Soft blocked: no') > 0:
            return 1
        else:
            return 0

    def was_toggled(self, state):
        if self.get_state() == state:
            return False
        else:
            return True

class Display(object):
    def __init__(self):
        self.original_active_monitors = self.get_active_monitor()

    def get_active_monitor(self):
        xrandr_cmd = "xrandr | awk '/ connected/ && /[[:digit:]]x[[:digit:]].*+/{print $1}'"
        out = subprocess.Popen(xrandr_cmd, shell=True, stdout=subprocess.PIPE)
        (stdout, stderr) = out.communicate()
        return stdout

    def trigger_display_switch (self):
        ''' Trigger super+p twice '''
        ui = UInput()
        ui.write(e.EV_KEY, e.KEY_LEFTMETA, 1)
        ui.syn()
        time.sleep(1)
        ui.write(e.EV_KEY, e.KEY_P, 1)
        ui.write(e.EV_KEY, e.KEY_P, 0)
        ui.write(e.EV_KEY, e.KEY_P, 1)
        ui.write(e.EV_KEY, e.KEY_P, 0)
        ui.write(e.EV_KEY, e.KEY_LEFTMETA, 0)
        ui.syn()
        ui.close()

class Brightness(object):
    def __init__(self, path):
        self.sysfs_path = path
        self.original_level = self.get_brightness()

    def read_value(self, path):
        bsys = open(path, 'r')
        lines = bsys.readlines()
        bsys.close()
        return int(''.join(lines).strip())

    def set_brightness(self, value):
        value = '%d' % value
        path = open(os.path.join(self.sysfs_path, 'brightness'), 'w')
        path.write(value)
        path.close()

    def get_max_brightness(self):
        full_path = os.path.join(self.sysfs_path, 'max_brightness')
        return self.read_value(full_path)

    def get_brightness(self):
        full_path = os.path.join(self.sysfs_path, 'brightness')
        return self.read_value(full_path)

    def restore_brightness(self):
        self.set_brightness(self.original_level)

    def was_brightness_applied(self, bl):
        # See if the selected brightness was applied
        #   Note: this doesn't guarantee that brightness changed.
        if self.get_brightness() != bl:
            return False
        return True

    def was_brightness_up(self, bl):
        if self.get_brightness() > bl:
            return True
        return False

    def was_brightness_down(self, bl):
        if self.get_brightness() < bl:
            return True
        return False

class Suspend(object):

    def prepare_to_sleep(self):
        # write a stamp for sleep time
        kmsg = open('/dev/kmsg', 'w')
        kmsg.write(os.path.basename(__file__) + ': prepare to sleep')
        kmsg.close()
        return 0

    def go_to_sleep(self):
        self.prepare_to_sleep()
        # Trigger an ACPI sleep button event
        acpidbg = Acpidbg('_SB.BTNV')
        acpidbg.run_command('2 0')
        # wait until OS handles events and transit to sleep
        time.sleep(10)
        return 0

    def get_sleep_time(self):
        cmd = "dmesg | grep 'prepare to sleep' | tail -1 | awk -F'[].[]' ' { print $2 }'"
        out = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        (stdout, stderr) = out.communicate()
        return int(stdout)

    def get_wakeup_time(self):
        cmd = "dmesg | grep 'PM: suspend exit' | tail -1 | awk -F'[].[]' ' { print $2 }'"
        out = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        (stdout, stderr) = out.communicate()
        return int(stdout)

    def set_wakeup_time(self, sec):
        subprocess.Popen('rtcwake --seconds %d' % sec, shell=True)
        return 0

def airplane_mode_test():
    '''
    This function triggers ACPI rfkill events to the Intel ACPI HID device and
    verifies whether WLAN and bluetooth's status is changed in rfkill accordingly.
    '''

    acpidbg = Acpidbg('_SB.HIDD.NRBT')
    wlan = Wireless("wlan")
    bluetooth = Wireless("bluetooth")

    # Toggle airplane modes by ACPI events
    wlan_state = wlan.get_state()
    bt_state = bluetooth.get_state()
    acpidbg.run_command()
    if not wlan.was_toggled(wlan_state) or not bluetooth.was_toggled(bt_state):
        return 1

    wlan_state = wlan.get_state()
    bt_state = bluetooth.get_state()
    acpidbg.run_command()
    if not wlan.was_toggled(wlan_state) or not bluetooth.was_toggled(bt_state):
        return 1

    return 0

def brightness_test():
    '''
    This function triggers ACPI brightness up and down events and
    verifies whether brightness levels are changed in sysfs accordingly.
    '''

    # Find intel or AMD backlight interface (they are mutually exclusive)
    find_bl = 'find /sys/class/backlight/ -name "[ai]*"'
    out = subprocess.Popen(find_bl, shell=True, stdout=subprocess.PIPE)
    (stdout, stderr) = out.communicate()

    # Prepare brightness interface
    brightness = Brightness(stdout.decode().strip())
    brightness.set_brightness(brightness.get_max_brightness() / 2)

    # Inialize for acpidbg
    method = '_SB.PCI0.GFX0.BRT6'
    acpi_dir = os.listdir('/sys/firmware/acpi/tables/')
    for file in acpi_dir:
        full_path = '/sys/firmware/acpi/tables/' + file
        if os.path.isdir(full_path):
            continue
        f = open(full_path, 'rb')
        s = f.read()
        if s.find(b'PC00GFX') > 0:
            method = '_SB.PC00.GFX0.BRT6'
        f.close()

    acpidbg = Acpidbg(method)

    # Test brightness up & down by ACPI control methods
    cur_bl = brightness.get_brightness()
    acpidbg.run_command('1 0')
    if not brightness.was_brightness_up(cur_bl):
        return 1

    cur_bl = brightness.get_brightness()
    acpidbg.run_command('2 0')
    if not brightness.was_brightness_down(cur_bl):
        return 1

    brightness.restore_brightness()
    return 0

def display_switch_test():
    '''
    This function generates 2 Super+P keycodes twice and
    verifies displays are changed in xrandr.

    Note: it requires an external monitor to be attached.
    '''

    display = Display()
    display.trigger_display_switch()
    time.sleep(5)
    if display.get_active_monitor() == display.original_active_monitors:
        return 1

    display.trigger_display_switch()
    time.sleep(5)
    if display.get_active_monitor() != display.original_active_monitors:
        return 1

    return 0

def keyboard_backlight_test():
    '''
    This function changes keyboard backlights in kbd_backlight
    sysfs and verified backlights are updated correctly.
    '''

    backlight = Brightness('/sys/class/leds/dell::kbd_backlight')
    backlight.set_brightness(0)

    for bl in range (0, backlight.get_max_brightness() + 1):
        backlight.set_brightness(bl)
        time.sleep(0.5)

        if not backlight.was_brightness_applied(bl):
            backlight.restore_brightness()
            return 1

    backlight.restore_brightness()
    return 0

def suspend_button_test():
    '''
    This function sets a wakeup time and triggers an ACPI sleep button events to
    verifies a system goes into sleep and then wakes up.
    '''

    suspend = Suspend()

    suspend.set_wakeup_time(60)
    suspend.go_to_sleep()
    if suspend.get_sleep_time() > suspend.get_wakeup_time():
        return 1

    return 0

def main():

    parser = argparse.ArgumentParser(description='Check Dell hotkey functionality.')
    parser.add_argument("-f", "--function", help="Function name", required=True)
    args = parser.parse_args()

    if args.function == "airplane_mode":
        exit_status = airplane_mode_test()
    elif args.function == "brightness":
        exit_status = brightness_test()
    elif args.function == "display_switch":
        exit_status = display_switch_test()
    elif args.function == "keyboard_backlight":
        exit_status = keyboard_backlight_test()
    elif args.function == "suspend_button":
        exit_status = suspend_button_test()

    exit(exit_status)

if __name__ == '__main__':
    main()
