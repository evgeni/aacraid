import subprocess
import re
import os

segmentfind = re.compile(r'(\d+,\d+)')

for p in os.environ['PATH'].split(os.path.pathsep)+['/usr/StorMan/']:
    if os.path.isfile(os.path.join(p, 'arcconf')):
        arcconf = os.path.join(p, 'arcconf')
        break

if not hasattr(subprocess, 'check_output'):
    # see https://gist.github.com/839684
    def check_output(*popenargs, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        return output
    subprocess.check_output = check_output

def get_val(string):
    return string.split(':')[1].strip()

def get_num_controllers():
    cmd = [arcconf, 'GETVERSION']
    ret = subprocess.check_output(cmd)
    for line in ret.splitlines():
        if line.startswith('Controllers found:'):
            num = get_val(line)
            return int(num)
    return 0

def get_controller_info(controllerid):
    cmd = [arcconf, 'GETCONFIG', str(controllerid), 'AD']
    ret = subprocess.check_output(cmd)
    model = serial = bios = firmware = driver = bootflash = lds = status = None
    id = 'c%i' % controllerid
    for line in ret.splitlines():
        line = line.strip()
        if line.startswith('Controller Model'):
            model = get_val(line)
        elif line.startswith('Controller Serial Number'):
            serial = get_val(line)
        elif line.startswith('BIOS'):
            bios = get_val(line)
        elif line.startswith('Firmware'):
            firmware = get_val(line)
        elif line.startswith('Driver'):
            driver = get_val(line)
        elif line.startswith('Boot Flash'):
            bootflash = get_val(line)
        elif line.startswith('Logical devices'):
            lds = int(get_val(line).split('/')[0])
        elif line.startswith('Controller Status'):
            status = get_val(line)
    return {'id': id, 'model': model, 'serial': serial, 'bios': bios, 'firmware': firmware,
            'driver': driver, 'bootflash': bootflash, 'lds': lds, 'status': status,
            'numid': controllerid}

def get_logicaldevice_info(controllerid, ldid):
    cmd = [arcconf, 'GETCONFIG', str(controllerid), 'LD', str(ldid)]
    ret = subprocess.check_output(cmd)
    id = 'c%iu%i' % (controllerid, ldid)
    level = status = size = None
    members = []
    for line in ret.splitlines():
        line = line.strip()
        if line.startswith('RAID level'):
            level = get_val(line)
        elif line.startswith('Status of logical device'):
            status = get_val(line)
        elif line.startswith('Size'):
            size = get_val(line)
        elif line.startswith('Segment'):
            segment = get_val(line)
            members.append(segmentfind.search(segment).group(1))
    return {'id': id, 'level': level, 'status': status, 'size': size, 'members': members}

def get_disks_info(controllerid):
    cmd = [arcconf, 'GETCONFIG', str(controllerid), 'PD']
    ret = subprocess.check_output(cmd)
    diskid = vendor = model = status = None
    disks = {}
    for line in ret.splitlines():
        line = line.strip()
        if line.startswith('Reported Channel,Device(T:L)'):
            line = line.replace('T:L', 'TL')
            diskid = get_val(line)
            diskid = diskid.split('(')[0]
        elif line.startswith('State'):
            status = get_val(line)
        elif line.startswith('Vendor'):
            vendor = get_val(line)
            if not vendor:
                vendor = "UNKNOWN"
        elif line.startswith('Model'):
            model = get_val(line)
            if not model:
                model = "UNKNOWN"
        if diskid and model and vendor and status:
            id = 'c%ip%s' % (controllerid, diskid.split(',')[1])
            disk = {'id': id, 'diskid': diskid, 'status': status, 'vendor': vendor, 'model': model}
            disks[diskid] = disk
            diskid = vendor = model = status = None
    return disks

def pretty_info(controllerid):
    output = []
    i = get_controller_info(controllerid)
    output.append("-- Controller information --")
    output.append("-- ID | Model | Status")
    output.append("%(id)s | %(model)s | %(status)s" % i)
    disks = get_disks_info(controllerid)
    output.append('-- Array information --')
    output.append('-- ID | Type | Size | Status')
    for l in range(0,i['lds']):
        li = get_logicaldevice_info(controllerid,l)
        output.append('%(id)s | %(level)s | %(size)s | %(status)s' % li)
        output.append('-- Disk information')
        output.append('-- ID | Vendor | Model | Status')
        for member in li['members']:
            output.append('%(id)s | %(vendor)s | %(model)s | %(status)s ' % disks[member])
    return '\n'.join(output)
