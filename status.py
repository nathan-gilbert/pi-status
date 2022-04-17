#!/usr/bin/python3
'''
Simple Raspberry Pi Web Status Page

Example usage: "python status.py > /var/wwww/html/status.html"

Originally script created by /u/TheLadDothCallMe
'''
from dis import dis
import time
import os
from subprocess import check_output
from string import Template
# Only used for getting the RAM values
import psutil
from enum import Enum


class Distro(Enum):
    UNKNOWN = 0
    RASPBIAN = 1
    OPENSUSE = 2
    OPENBSD = 3
    NETBSD = 4


def read_template(template_path):
    with open(template_path) as template:
        return template.read()


def render(template_path, **kwargs):
    return Template(read_template(template_path)).substitute(**kwargs)


def save_ping(outfile, ping_value):
    """Saves the ping value out to a file"""
    with open(outfile, 'a') as ping_file:
        ping_file.writelines(str(ping_value))


def read_ping(infile):
    """Read in the ping history and return an avg value"""
    lines = []
    with open(infile, 'r') as ping_file:
        lines = [x.strip() for x in ping_file.readlines()]
        lines = list(filter(lambda x: x != '', lines))

    total = sum(map(lambda x: float(x.strip()), lines))
    return str(total / len(lines))


def determine_distro() -> Distro:
    distro_string = ""
    if os.path.isfile('/etc/issue'):
        distro_string = check_output(["cat", "/etc/issue"]).decode().strip()
    else:
        distro_string = check_output(["uname", "-a"]).decode().strip()

    if distro_string.find("Raspbian") > -1:
        return Distro.RASPBIAN
    elif distro_string.find("openSUSE") > -1:
        return Distro.OPENSUSE
    elif distro_string.find('OpenBSD') > -1:
        return Distro.OPENBSD
    else:
        return Distro.UNKNOWN


def get_image_file(distro: Distro) -> str:
    if distro == Distro.RASPBIAN:
        return "raspberry-pi-logo.png"
    elif distro == Distro.OPENSUSE:
        return "opensuse-logo.png"
    elif distro == Distro.OPENBSD:
        return "openbsd-logo.png"
    return "raspberry-pi-logo.png"


def get_disk_name(distro: Distro) -> str:
    if distro == Distro.RASPBIAN:
        return "/dev/root"
    elif distro == Distro.OPENSUSE:
        return "/"
    elif distro == Distro.OPENBSD:
        return "/dev/sd1h"
    return "/dev/root"


def get_usb_name(distro: Distro) -> str:
    if distro == Distro.RASPBIAN:
        return "/dev/sda1"
    elif distro == Distro.OPENSUSE:
        return "/"
    elif distro == Distro.OPENBSD:
        return ""
    return "/dev/sda1"


def get_output_dir(distro: Distro) -> str:
    if distro == Distro.RASPBIAN:
        return "/var/www/html"
    elif distro == Distro.OPENSUSE:
        return "/srv/www/htdocs"
    elif distro == Distro.OPENBSD:
        return "/var/www/htdocs/pi-status"
    return "/var/www/html"

def get_logo_width(distro: Distro) -> str:
    if distro == Distro.RASPBIAN:
        return "200"
    elif distro == Distro.OPENSUSE:
        return "200"
    elif distro == Distro.OPENBSD:
        return "350"
    return "200"


def disk_space(drive):
    """Returns the disk space used and free in a tuple of the supplied drive"""
    lines = []
    disk_percent = "0"
    disk_used = "0"
    disk_free = "0"
    disk_total = "0"
    disk_space_lines = check_output(["df", "-h"])
    lines = disk_space_lines.decode("utf-8").split("\n")
    for l in lines:
        if l.startswith(drive):
            tokens = l.split()
            disk_used = str(tokens[2])
            disk_free = str(tokens[3])
            disk_total = str(tokens[1])
            disk_percent = str(tokens[4].replace("%", ""))
            break
    return (disk_total, disk_used, disk_free, disk_percent)


def get_cpu_temp(distro) -> str:
    temp_c = ""
    if distro == Distro.RASPBIAN:
        temp_c = str(round(float(check_output(
            ["cat", "/sys/class/thermal/thermal_zone0/temp"])) / 1000, 1))
    elif distro == Distro.OPENSUSE:
        temp_c = str(round(float(check_output(
            ["cat", "/sys/class/thermal/thermal_zone0/temp"])) / 1000, 1))
    elif distro == Distro.OPENBSD:
        temp_c_string = str(check_output(["sysctl -a | grep temperature"], shell=True).decode().strip())
        temp_c_string = temp_c_string.replace("hw.sensors.acpitz0.temp0=", "")
        temp_c_string = temp_c_string.replace(" degC (zone temperature)", "")
        temp_c = temp_c_string
    else:
        temp_c = "-1"
    return temp_c


if __name__ == "__main__":
    # Just shows the hostname command. Note the .split() function to get rid
    # of any new lines from the shell.
    hostname = check_output(["hostname"]).decode().strip()

    cpu_used = psutil.cpu_percent()

    # The calculations here are just lazy and round to the nearest integer.
    ram_total = str(psutil.virtual_memory().total / 1024 / 1024)
    ram_used = str((psutil.virtual_memory().total -
                    psutil.virtual_memory().available) / 1024 / 1024)
    ram_free = str(psutil.virtual_memory().available / 1024 / 1024)
    ram_percent = str(psutil.virtual_memory().percent)

    # Shows the uptime from the shell with the pretty option
    uptime = check_output(["uptime", ""]).decode().strip()

    # The last time the script was run
    updated = time.strftime("%I:%M:%S %p %m/%d/%Y %Z")

    distro = determine_distro()
    out_dir = get_output_dir(distro)

    # Reads the CPU temp in milligrade
    temp_c = get_cpu_temp(distro)
    temp_f = float(temp_c) * 1.8 + 32
    temp_f = "{:.2f}".format(temp_f)

    # Pings Google DNS 5 times and awks the average ping time
    google_ping = check_output(
        ["ping -c 5 8.8.8.8 | tail -1| awk -F '/' '{print $5}'"], shell=True).decode()
    save_ping(f"{out_dir}/google_ping_history.txt", google_ping)
    google_ping = "{:.2f}".format(float(google_ping))
    google_avg_ping = read_ping(f"{out_dir}/google_ping_history.txt")
    google_avg_ping = "{:.2f}".format(float(google_avg_ping))

    image_file = get_image_file(distro)
    disk_name = get_disk_name(distro)
    usb_name = get_usb_name(distro)

    # get the storage space used
    root_space = disk_space(disk_name)
    usb_space = disk_space(usb_name)

    image_width=get_image_width(distro)

    print(render(template_path="index.template.html",
                 image_file=image_file,
                 image_wdith=image_width,
                 hostname=hostname,
                 uptime=uptime,
                 cpu_used=cpu_used,
                 temp_c=temp_c,
                 temp_f=temp_f,
                 ram_used=ram_used,
                 ram_free=ram_free,
                 ram_total=ram_total,
                 ram_percent=ram_percent,
                 root_space_0=root_space[0],
                 root_space_1=root_space[1],
                 root_space_2=root_space[2],
                 root_space_3=root_space[3],
                 usb_space_0=usb_space[0],
                 usb_space_1=usb_space[1],
                 usb_space_2=usb_space[2],
                 usb_space_3=usb_space[3],
                 google_avg_ping=google_avg_ping,
                 google_ping=google_ping,
                 last_updated=updated))
