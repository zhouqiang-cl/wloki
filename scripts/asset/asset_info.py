#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import time
import os
import signal


class classproperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def check_output(command, shell=False, timeout=5):
    p = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, preexec_fn=os.setpgrp)
    starttime = time.time()
    while True:
        returncode = p.poll()
        if returncode is not None:
            break
        if time.time() - starttime > timeout:
            os.killpg(p.pid, signal.SIGKILL)
            raise subprocess.CalledProcessError(p.returncode, command)
        time.sleep(0.1)

    stdout = p.stdout.read()
    if p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, command)
    return stdout


def split_n_strip(string, sep):
    return [n.strip() for n in string.split(sep) if n.strip()]


class SystemInfoFetcher(object):
    DMID_TOOL_PATH = "/usr/sbin/dmidecode"
    IPMI_TOOL_PATH = "/usr/bin/ipmitool"
    MEGACLI_PATH = "/sbin/MegaCli"
    LSB_TOOL = "/usr/bin/lsb_release"
    VIRSH_PATH = "/usr/bin/virsh"
    DMID_COMMAND = [DMID_TOOL_PATH, "-s"]
    SN_FILE_PATH = "/etc/sn"

    @classmethod
    def get_dmid_info(cls, name):
        command = cls.DMID_COMMAND + [name]
        return check_output(command).strip()

    @classproperty
    def hostname(cls):
        import socket
        return socket.gethostname()

    @classproperty
    def idc(cls):
        return cls.hostname.rsplit('.', 1)[1]

    @classproperty
    def sn(cls):
        sn = cls.get_dmid_info('system-serial-number')
        if sn == "Not Specified":
            with open(cls.SN_FILE_PATH) as sn_file:
                sn = sn_file.read().strip()
        return sn

    @classproperty
    def server_type(cls):
        import re
        product_name = cls.get_dmid_info('system-product-name')
        if re.match('(HVM|KVM|Bichs)', product_name):
            return 'vm'
        elif 'vmh' in cls.hostname:
            return 'kvm'
        else:
            return 'raw'

    @classproperty
    def system_product_name(cls):
        product_name = cls.get_dmid_info('system-product-name')
        return product_name

    @classproperty
    def ilo_ip(cls):
        command = "{0} lan print | grep 'IP Address' | grep -Po '\d+\.\d+\.\d+\.\d+'" \
            .format(cls.IPMI_TOOL_PATH)
        try:
            if cls.server_type not in ('kvm', 'raw'):
                return None
            return check_output(command, shell=True).strip()
        except subprocess.CalledProcessError as e:
            # TODO: log here
            return None

    @classproperty
    def vms(cls):
        if cls.server_type != "kvm":
            return None
        ret = []
        list_vm_command = "{0} list | awk '$1 ~ /[0-9]+/{{print $2}}'".format(cls.VIRSH_PATH)
        try:
            vm_names = split_n_strip(check_output(list_vm_command, shell=True), "\n")
            for vm in vm_names:
                query_vm_mac_command = "{0} domiflist {1} | awk --re-interval '$5 ~ /[0-9a-zA-Z]{{2}}:/{{print $5}}'" \
                    .format(cls.VIRSH_PATH, vm)
                macs = split_n_strip(check_output(query_vm_mac_command, shell=True), "\n")
                ret.append({"vm_name": vm, "mac": macs})
            return ret
        except subprocess.CalledProcessError as e:
            # TODO: log here
            return None

    @classproperty
    def kernel(cls):
        import os
        sysname, _, release, _, _ = os.uname()
        return " ".join([sysname, release])

    @classproperty
    def manufacturer(cls):
        name = cls.get_dmid_info('system-manufacturer')
        return name

    @classproperty
    def cpu_model(cls):
        model = set(n.strip() for n in cls.get_dmid_info('processor-version').split('\n'))
        return list(model)

    @classproperty
    def os(cls):
        command = "{0} -d | sed -e 's/Description:\s\+//g'".format(cls.LSB_TOOL)
        try:
            return check_output(command, shell=True).strip()
        except subprocess.CalledProcessError as e:
            # TODO: log here
            return None

    @classproperty
    def hard_disk_num(cls):
        command = "{0} -PDList -aALL | egrep -E 'Device Id: [0-9]+' | wc -l".format(cls.MEGACLI_PATH)
        if cls.server_type == "vm":
            return None
        else:
            try:
                return int(check_output(command, shell=True, timeout=2).strip())
            except (subprocess.CalledProcessError, ValueError) as e:
                # TODO: log here
                return None

    @classproperty
    def hard_disk_size(cls):
        command = """{0} -PDList -aALL |grep 'Raw Size:'| egrep -o -E '[0-9\.]+\s(GB|TB|MB)' | uniq -c |
         awk '{{print $1, "x", $2, $3}}'""".format(cls.MEGACLI_PATH)
        if cls.server_type == "vm":
            return None
        else:
            try:
                return split_n_strip(check_output(command, shell=True, timeout=2), "\n")
            except subprocess.CalledProcessError as e:
                # TODO: log here
                return None


# asset agent acquire json data from this function
def export():
    ret = {
        "data": {
            "sn": SystemInfoFetcher.sn,
            "hostname": SystemInfoFetcher.hostname,
            "manu": SystemInfoFetcher.manufacturer,
            "cpuModel": SystemInfoFetcher.cpu_model,
            "os": SystemInfoFetcher.os,
            "kernel": SystemInfoFetcher.kernel,
            "ilo_ip": SystemInfoFetcher.ilo_ip,
            "type": SystemInfoFetcher.server_type,
            "idc": SystemInfoFetcher.idc,
            "vms": SystemInfoFetcher.vms,
            "system_product_name": SystemInfoFetcher.system_product_name,
            "hard_disk_num": SystemInfoFetcher.hard_disk_num,
            "hard_disk_size": SystemInfoFetcher.hard_disk_size,
        },
        "expire": 3600 * 24,
    }

    if SystemInfoFetcher.server_type == "kvm":
        ret['expire'] = 300

    return ret


if __name__ == "__main__":
    import pprint

    pprint.pprint(export())
