#!/usr/bin/env python
import traceback
import rrdtool
import os, time
import psutil

RUNDIR = os.path.dirname(os.path.realpath(__file__))
RRDSDIR = os.path.join(RUNDIR, 'rrds')
cpuRRDFile = os.path.join(RRDSDIR, 'cpustatus.rrd')
memRRDFile = os.path.join(RRDSDIR, 'meminfo.rrd')
uptimeRRDFile = os.path.join(RRDSDIR, 'uptime.rrd')
mountRRDFile = os.path.join(RRDSDIR, 'mount-%s.rrd')
netRRDFile = os.path.join(RRDSDIR, 'interface-%s.rrd')
diskRRDFile = os.path.join(RRDSDIR, 'hdd-%s.rrd')


# Archive format
archiveFormat = [
    'RRA:AVERAGE:0.5:1:864', #5-minute for 3 days
    'RRA:AVERAGE:0.5:3:1344', #15-minute for 2 weeks
    'RRA:AVERAGE:0.5:12:1488', #1-hour for 2 months
    'RRA:AVERAGE:0.5:36:2960'] #3-hour for 1 year

# step - time itervals in seconds for data in rrd  table
step = 300
hearbeat = step*2

def updateRRD (filename, data, type, low = 'U', up = 'U'):
    if not os.path.isfile(filename):
        DS = ['DS:%s:%s:%d:%s:%s'%(par,type,hearbeat,low,up) for par in data.keys()]
        ret = rrdtool.create(filename, '--step', str(step),
                *(DS + archiveFormat))
        if ret:
            print rrdtool.error()
            return False

    ret = rrdtool.update(filename, '--template', ":".join(data.keys()), 'N:' + ':'.join(map(str,data.values())))
    if ret:
        print rrdtool.error()
        return False

    return True

#def updateCPURRD(ctemp, cusage, pids):
#    createRRDfile(CpuRRDFile, ['cpuTemp', 'cpuUsage', 'pids'], 'GAUGE', '0', 'U')
#
#    #update data
#    ret =rrdtool.update(CpuRRDFile, 'N:%s:%s:%s' %(ctemp, cusage, pids))
#    if ret:
#        print rrdtool.error()
#        return False
#
#    return True
#
#def updateUptimeRRD(uptime):
#    createRRDfile(UptimeRRDFile, ['uptime'], 'GAUGE', '0', 'U')
#
#    #update data
#    ret = rrdtool.update(UptimeRRDFile, 'N:%s' %(uptime))
#    if ret:
#        print rrdtool.error()
#        return False
#
#    return True
#
#def updateMemRRD(total, used, buf, cached, free):
#    createRRDfile(MemRRDFile, ['total', 'used', 'buf', 'cached', 'free'], 'GAUGE', '0', 'U')
#
#    #update data
#    ret = rrdtool.update(MemRRDFile, 'N:%s:%s:%s:%s:%s' %(total, used, buf, cached, free))
#    if ret:
#        print rrdtool.error()
#        return False
#    return True
#
#def updatePartitionRRD(index, total, used, free, percent):
#    filename = MountRRDFile%(index)
#    createRRDfile(filename, ['total', 'used', 'free', 'percent'], 'GAUGE', '0', 'U')
#
#    #update data
#    ret = rrdtool.update(MountRRDFile, 'N:%s:%s:%s:%s' %(total, used, free, percent))
#    if ret:
#        print rrdtool.error()
#        return False
#    return True
#
#def updateNetRRD(net, send, recv):
#    filename = NetRRDFile%(net)
#    createRRDfile(filename, ['send', 'recv'], 'DERIVE', '0', 'U')
#
#    #update data
#    ret = rrdtool.update(NetRRDFile, 'N:%s:%s' %(send, recv))
#    if ret:
#        print rrdtool.error()
#        return False
#    return True
#
#def updateDiskRRD(name, rcount, wcount, rbytes, wbytes,
#        rtime, wtime):
#    filename = DiskRRDFile%(name)
#    createRRDfile(filename, ['rcount', 'wcount', 'rbytes', 'wbytes', 'rtime', 'wtime'], 'DERIVE', '0', 'U')
#
#    #update data
#    ret = rrdtool.update(filename,
#            'N:%s:%s:%s:%s:%s:%s' %(rcount, wcount, rbytes, wbytes, rtime, wtime))
#    if ret:
#        print rrdtool.error()
#        return False
#    return True

def get_cpu_temp():
    tempfile = '/sys/class/thermal/thermal_zone0/temp'
    if os.path.isfile(tempfile):
        tf = open(tempfile)
        cpu_temp = tf.read()
        tf.close()
        return float(cpu_temp)/1000.0
    else:
        return 'U'

#get CPU info
def getCpuInfo():
    cpu_info = {'cpuTemp' : 'U', 'cpuUsage' : 'U', 'pids' : 'U'}
    time.sleep(3)
    try:
        cpu_info['cpuUsage'] = psutil.cpu_percent()
        cpu_info['cpuTemp'] = get_cpu_temp()
        cpu_info['pids'] = len(psutil.pids())
    except Exception, err:
        print 'Something goes wrong in getCpuInfo. err = ' + str(err)
    updateRRD(cpuRRDFile, cpu_info, 'GAUGE', '0', 'U')



#get uptime info
def getUptimeInfo():
    uptime_info = {'uptime' : 'U'}
    try:
        uptime = int(time.time() - psutil.boot_time())/60 #uptime in minutes
    except Exception, err:
        print 'Something goes wrong in getUptimeInfo. err = ' + str(err)
    updateRRD(uptimeRRDFile, uptime_info, 'GAUGE', '0', 'U')

# get RAM info
def getMemInfo():
    '''
    svmem(total=508686336L, available=432787456L, percent=14.9, used=480034816L, free=28651520L, active=214945792, inactive=228995072, buffers=43900928L, cached=360235008)
    '''
    mem_info= {'total' : 'U', 'used' : 'U', 'buf' : 'U', 'cached' : 'U', 'free' : 'U'}
    try:
        mem = psutil.phymem_usage()
        mem_info['total'] = mem.total
        mem_info['used'] = mem.used
        #TODO mem_info['buf'] = mem.buffers
        #mem_info['cached'] = mem.cached
        mem_info['free'] = mem.total - mem.used
    except Exception, err:
        print 'Something goes wrong in getMemInfo. err = ' + str(err)
    updateRRD(memRRDFile, mem_info, 'GAUGE', '0', 'U')

# get mount info
#sdiskusage(total=7764254720L, used=3972837376L, free=3429568512L, percent=51.2)
def getMountInfo():
    try:
        disks = psutil.disk_partitions()
        for d in disks:
            mount_info = {'total' : 'U', 'used' : 'U', 'free' : 'U', 'percent' : 'U'}
            mpoint = d.mountpoint
            if mpoint == '/':
                index = "root"
            else:
                index = mpoint.split('/')[-1]

            try:
                diskInfo = psutil.disk_usage(mpoint)
                mount_info['total'] = diskInfo.total
                mount_info['used'] = diskInfo.used
                mount_info['free'] = diskInfo.free
                mount_info['percent'] = float(diskInfo.percent)
            except Exception, err:
                print 'Something wrong with psutils.disk_usage for disk %s. err = '%d + str(err)

            updateRRD(mountRRDFile%(index), mount_info, 'GAUGE', '0', 'U')
    except Exception, err:
        print "Can't mange with psutil.disk_partitions. err = " + str(err)

# get net info
#snetio(bytes_sent=42988, bytes_recv=42988, packets_sent=595, packets_recv=595, errin=0, errout=0, dropin=0, dropout=0)
def getNetInfo():
    try:
        nets = psutil.net_io_counters(pernic=True)
        for net in nets.keys():
            if net == 'lo':
                continue
            net_info = {'send' : 'U', 'recv' : 'U'}
            try:
                info = nets.get(net)
                net_info['send'] = info.bytes_sent
                net_info['recv'] = info.bytes_recv
            except Exception, err:
                print 'Something wrong in getNetInfo, net = %s. err = '%net + str(err)
            updateRRD(netRRDFile%(net), net_info, 'DERIVE', '0', 'U')
    except Exception, err:
        print "Can't manage with psutil.net_io_counters. err = " + str(err)

#get disk info
#    filename = DiskRRDFile%(name)
#    createRRDfile(filename, ['rcount', 'wcount', 'rbytes', 'wbytes', 'rtime', 'wtime'], 'DERIVE', '0', 'U')
#sdiskio(read_count=9837, write_count=43761, read_bytes=198268416, write_bytes=933855232, read_time=87870, write_time=35913990)
def getDiskInfo():
    try:
        disks = psutil.disk_io_counters(perdisk=True)
        for dname in disks.keys():
            disk_info = {'rcount' : 'U', 'wcount' : 'U', 'rbytes' : 'U', 'wbytes' : 'U', 'rtime' : 'U', 'wtime' : 'U'}
            try:
                diskio = disks.get(dname)
                disk_info['rcount'] =  diskio.read_count
                disk_info['wcount'] =  diskio.write_count
                disk_info['rbytes'] =  diskio.read_bytes
                disk_info['wbytes'] =  diskio.write_bytes
                disk_info['rtime'] =  diskio.read_time
                disk_info['wtime'] =  diskio.write_time
            except Exception, err:
                print 'Something wrong while read disk info %s. err = '%dname + str(err)
            updateRRD(diskRRDFile%(dname), disk_info, 'DERIVE', '0', 'U')
    except Exception, err:
        print "Can't manage with psutil.disk_io_counters. err = " + str(err)


def test():
    print 'test....'
    getNetInfo()

def main():

    getCpuInfo()
    getUptimeInfo()
    getMemInfo()
    getDiskInfo()
    getMountInfo()
    getNetInfo()


if __name__ == '__main__':
    main()
    #test()
