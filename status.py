#!/usr/bin/python3
'''
Simple Raspberry Pi Web Status Page

Example usage: "python status.py > /var/wwww/html/status.html"

Originally script created by /u/TheLadDothCallMe
'''
import time
from subprocess import check_output
from string import Template
# Only used for getting the RAM values
import psutil


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
        # print line
        if l.startswith(drive):
            #tokens = map(lambda x: x.replace("G", "").replace("M", ""), line.split())
            tokens = l.split()
            disk_used = str(tokens[2])
            disk_free = str(tokens[3])
            disk_total = str(tokens[1])
            disk_percent = str(tokens[4].replace("%", ""))
            break
    return (disk_total, disk_used, disk_free, disk_percent)


if __name__ == "__main__":
    # Just shows the hostname command. Note the .split() function to get rid
    # of any new lines from the shell.
    hostname = check_output(["hostname"]).decode().strip()

    # The calculations here are just lazy and round to the nearest integer.
    ram_total = str(psutil.virtual_memory().total / 1024 / 1024)
    ram_used = str((psutil.virtual_memory().total -
                    psutil.virtual_memory().available) / 1024 / 1024)
    ram_free = str(psutil.virtual_memory().available / 1024 / 1024)
    ram_percent = str(psutil.virtual_memory().percent)

    # Shows the uptime from the shell with the pretty option
    uptime = check_output(["uptime", "-p"]).decode().strip()

    # The last time the script was run
    updated = time.strftime("%I:%M:%S %p %m/%d/%Y %Z")

    # Reads the CPU temp in milligrade
    temp_c = str(round(float(check_output(
        ["cat", "/sys/class/thermal/thermal_zone0/temp"])) / 1000, 1))
    temp_f = str(float(temp_c) * 1.8 + 32)

    # Pings Google DNS 5 times and awks the average ping time
    google_ping = check_output(
        ["ping -c 5 8.8.8.8 | tail -1| awk -F '/' '{print $5}'"], shell=True).decode()
    save_ping("/var/www/html/google_ping_history.txt", google_ping)
    google_avg_ping = read_ping("/var/www/html/google_ping_history.txt")

    # Pings century link
    isp_ping = check_output(
        ["ping -c 5 205.171.3.25 | tail -1| awk -F '/' '{print $5}'"], shell=True).decode()
    save_ping("/var/www/html/isp_ping_history.txt", isp_ping)
    isp_avg_ping = read_ping("/var/www/html/isp_ping_history.txt")

    # get the storage space used
    root_space = disk_space("/dev/root")
    usb_space = disk_space("/dev/sda1")

    fail2ban_lines = []
    with open("/var/log/fail2ban.log", 'r') as inFile:
        fail2ban_lines = inFile.readlines()

    today = time.strftime("%Y-%m-%d")
    banned_ips = 0
    for line in fail2ban_lines:
        if line.startswith(today):
            if line.find("Ban") > -1:
                banned_ips += 1

    print(render(template_path="index.template.html",
                 hostname=hostname,
                 ram_percent=ram_percent,
                 uptime=uptime,
                 temp_c=temp_c,
                 temp_f=temp_f,
                 ram_used=ram_used,
                 ram_total=ram_total,
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
                 isp_ping=isp_ping,
                 isp_avg_ping=isp_avg_ping,
                 banned_ips=banned_ips,
                 last_updated=updated))
