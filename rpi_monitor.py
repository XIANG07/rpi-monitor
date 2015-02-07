#!/usr/bin/env python
import os, time, re
import rrdtool
import psutil

RUNDIR = os.path.dirname(os.path.realpath(__file__))
RRDSDIR = os.path.join(RUNDIR, 'rrds')
cpuRRDFile = os.path.join(RRDSDIR, 'cpustatus.rrd')
cpuTempRRDFile = os.path.join(RRDSDIR, 'cputemp.rrd')
pidsRRDFile = os.path.join(RRDSDIR, 'pids.rrd')
memRRDFile = os.path.join(RRDSDIR, 'meminfo.rrd')
uptimeRRDFile = os.path.join(RRDSDIR, 'uptime.rrd')
mountRRDFile = os.path.join(RRDSDIR, 'mount-%s.rrd')
netRRDFile = os.path.join(RRDSDIR, 'interface-%s.rrd')
diskRRDFile = os.path.join(RRDSDIR, 'hdd-%s.rrd')

archivePeriods = [
    '0.5:1:864', #5-minute for 3 days
    '0.5:3:1344', #15-minute for 2 weeks
    '0.5:12:1488', #1-hour for 2 months
    '0.5:36:2960'] #3-hour for 1 year

# step - time itervals in seconds for data in rrd  table
step = 300
hearbeat = step*2

def updateRRD (filename, data, _type, low = 'U', up = 'U', atype = 'AVERAGE'):
    if not os.path.isfile(filename):
        if type(_type) is not dict:
            _type = dict.fromkeys(data, _type)
        if type(low) is not dict:
            low = dict.fromkeys(data, low)
        if type(up) is not dict:
            up = dict.fromkeys(data, up)
        DS = ['DS:%s:%s:%d:%s:%s'%(par, _type[par], hearbeat, low[par], up[par]) for par in data.keys()]
        RRA = ['RRA:%s:%s'%(atype, per) for per in archivePeriods]
        ret = rrdtool.create(filename, '--step', str(step),
                *(DS + RRA))
        if ret:
            print rrdtool.error()
            return False

    ret = rrdtool.update(filename, '--template', ":".join(data.keys()), 'N:' + ':'.join(map(str,data.values())))
    if ret:
        print rrdtool.error()
        return False

    return True


#get CPU info
def getCpuInfo():
    try:
        cpu_info = dict(psutil.cpu_times().__dict__)
        for k in cpu_info.keys():
            cpu_info[k] = int(cpu_info[k])
        updateRRD(cpuRRDFile, cpu_info, 'DERIVE', '0', 'U')
    except Exception, err:
        print 'Something goes wrong in getCpuInfo. err = ' + str(err)


def getCpuTempInfo():
    try:
        tempfile = '/sys/class/thermal/thermal_zone0/temp'
        if os.path.isfile(tempfile):
            cpu_temp = open(tempfile).read()/1000.0
        else:
            cpu_temp = 'U'
        cputemp_info = {'cpuTemp' : cpu_temp}
        updateRRD(cpuTempRRDFile, cputemp_info, 'GAUGE', '0', '100')
    except Exception, err:
        print 'Something goes wrong in getCpuTempInfo. err = ' + str(err)


def getPidsInfo():
    try:
        pids_info = {'pids' : len(psutil.pids())}
        updateRRD(pidsRRDFile, pids_info, 'GAUGE', '0', 'U')
    except Exception, err:
        print 'Something goes wrong in getPidsInfo. err = ' + str(err)

#get uptime info
def getUptimeInfo():
    try:
        uptime_info = {'uptime' : int(time.time() - psutil.boot_time())/60} #uptime in minutes
        updateRRD(uptimeRRDFile, uptime_info, 'GAUGE', '0', 'U', 'LAST')
    except Exception, err:
        print 'Something goes wrong in getUptimeInfo. err = ' + str(err)

# get RAM info
def getMemInfo():
    try:
        mem_info = dict(psutil.virtual_memory().__dict__)
        updateRRD(memRRDFile, mem_info, 'GAUGE', '0', 'U')
    except Exception, err:
        print 'Something goes wrong in getMemInfo. err = ' + str(err)

# get mount info
def getMountInfo():
    try:
        disks = psutil.disk_partitions()
        for d in disks:
            mpoint = d.mountpoint
            if mpoint == '/':
                index = "root"
            else:
                index = mpoint.split('/')[-1]
            try:
                mount_info = dict(psutil.disk_usage(mpoint).__dict__)
                updateRRD(mountRRDFile%(index), mount_info, 'GAUGE', '0', 'U')
            except Exception, err:
                print 'Something wrong with psutils.disk_usage for disk %s. err = '%d.mountpoint + str(err)

    except Exception, err:
        print "Can't mange with psutil.disk_partitions. err = " + str(err)

# get net info
def getNetInfo():
    try:
        nets = psutil.net_io_counters(pernic=True)
        for net in nets.keys():
            if re.match(r'lo\d*', net):
                continue
            try:
                net_info = dict(nets[net].__dict__)
                updateRRD(netRRDFile%(net), net_info, 'DERIVE', '0', 'U')
            except Exception, err:
                print 'Something wrong in getNetInfo, net = %s. err = '%net + str(err)
    except Exception, err:
        print "Can't manage with psutil.net_io_counters. err = " + str(err)

#get disk info
def getDiskInfo():
    try:
        disks = psutil.disk_io_counters(perdisk=True)
        for dname in disks.keys():
            try:
                disk_info = dict(disks.get(dname).__dict__)
                updateRRD(diskRRDFile%(dname), disk_info, 'DERIVE', '0', 'U')
            except Exception, err:
                print 'Something wrong while read disk info %s. err = '%dname + str(err)
    except Exception, err:
        print "Can't manage with psutil.disk_io_counters. err = " + str(err)


def test():
    print 'test....'
    getNetInfo()

def main():

    getCpuInfo()
    getCpuTempInfo()
    getPidsInfo()
    getUptimeInfo()
    getMemInfo()
    getDiskInfo()
    getMountInfo()
    getNetInfo()


if __name__ == '__main__':
    main()
    #test()
