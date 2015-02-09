#!/usr/bin/env python
import sys, os, time, re, sets
import rrdtool
import psutil

RUNDIR = os.path.dirname(os.path.realpath(__file__))
#paths for rrd files
RRDSDIR = os.path.join(RUNDIR, 'rrds')
cpuRRDFile = os.path.join(RRDSDIR, 'cpustatus.rrd')
cpuTempRRDFile = os.path.join(RRDSDIR, 'cputemp.rrd')
pidsRRDFile = os.path.join(RRDSDIR, 'pids.rrd')
memRRDFile = os.path.join(RRDSDIR, 'meminfo.rrd')
uptimeRRDFile = os.path.join(RRDSDIR, 'uptime.rrd')
mountRRDFile = os.path.join(RRDSDIR, 'mount-%s.rrd')
netRRDFile = os.path.join(RRDSDIR, 'interface-%s.rrd')
diskRRDFile = os.path.join(RRDSDIR, 'hdd-%s.rrd')

#paths for graph reports
REPORTDIR = os.path.join(RUNDIR, 'report')
memPNGFile = os.path.join(REPORTDIR, 'meminfo%s.png')
uptimePNGFile = os.path.join(REPORTDIR, 'uptime%s.png')
mountUsagePNGFile = os.path.join(REPORTDIR, 'mountusage%s.png')
netPNGFile = os.path.join(REPORTDIR, 'interface-%s%s.png')
diskIOPNGFile = os.path.join(REPORTDIR, 'hddio-%s%s.png')
cpuTempPNGFile = os.path.join(REPORTDIR, 'cputemp%s.png')
cpuPNGFile = os.path.join(REPORTDIR, 'cpuusage%s.png')
pidsPNGFile = os.path.join(REPORTDIR, 'pids.png')

archivePeriods = [
    '0.5:1:864', #5-minute for 3 days
    '0.5:3:1344', #15-minute for 2 weeks
    '0.5:12:1488', #1-hour for 2 months
    '0.5:36:2960'] #3-hour for 1 year

# step - time itervals in seconds for data in rrd  table
step = 300
hearbeat = step*2

gWidth='600'
gHeight='200'

#colors for graphs
cRED='#FF0000'
cGREEN='#00FF00'
cBLUE='#0000FF'
cMAGENTA='#FF00FF'
cLIGHTBLUE='#0A84C6'
cORANGE='#DD7C00'
cPURPLE='#7A0FE2'
#cBROWN='#842B00'
#cPINK='#FF00FF'
#cBLACK='#000000'
cGRAY='#AAAAAA'
#cTrans='#0000FF80'
cList=[cRED, cBLUE, cGREEN, cORANGE, cMAGENTA, cLIGHTBLUE, cPURPLE, cGRAY]
cTotal = len(cList)
cIndex = -1

### functions to work with colormaps ###
def colorNext ():
    global cIndex
    cIndex = cIndex + 1
    if cIndex >= cTotal:
        cIndex = 0
    return cList[cIndex]

def colorReset():
    global cIndex
    cIndex = -1

def colorCurrent():
    global cIndex
    if cIndex == -1:
        cIndex = 0;
    return cList[cIndex]


### functions for psutil data collecting and rrdtool database updates ###
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
    cpu_info = dict(psutil.cpu_times().__dict__)
    for k in cpu_info.keys():
        cpu_info[k] = int(cpu_info[k])
    updateRRD(cpuRRDFile, cpu_info, 'DERIVE', '0', 'U')

def getCpuTempInfo():
    tempfile = '/sys/class/thermal/thermal_zone0/temp'
    if os.path.isfile(tempfile):
        cpu_temp = open(tempfile).read()/1000.0
    else:
        cpu_temp = 'U'
    cputemp_info = {'cpuTemp' : cpu_temp}
    updateRRD(cpuTempRRDFile, cputemp_info, 'GAUGE', '0', '100')

def getPidsInfo():
    pids_info = {'pids' : len(psutil.pids())}
    updateRRD(pidsRRDFile, pids_info, 'GAUGE', '0', 'U')

#get uptime info
def getUptimeInfo():
    #uptime in minutes
    uptime_info = {'uptime' : int(time.time() - psutil.boot_time())/60}
    updateRRD(uptimeRRDFile, uptime_info, 'GAUGE', '0', 'U', 'LAST')

#get RAM info
def getMemInfo():
    mem_info = dict(psutil.virtual_memory().__dict__)
    updateRRD(memRRDFile, mem_info, 'GAUGE', '0', 'U')

#get mount info
def getMountInfo():
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

#get net info
def getNetInfo():
    nets = psutil.net_io_counters(pernic=True)
    for net in nets.keys():
        if re.match(r'lo\d*', net):
            continue
        try:
            net_info = dict(nets[net].__dict__)
            updateRRD(netRRDFile%(net), net_info, 'DERIVE', '0', 'U')
        except Exception, err:
            print 'Something wrong in getNetInfo, net = %s. err = '%net + str(err)

#get disk info
def getDiskInfo():
    disks = psutil.disk_io_counters(perdisk=True)
    for dname in disks.keys():
        try:
            disk_info = dict(disks.get(dname).__dict__)
            updateRRD(diskRRDFile%(dname), disk_info, 'DERIVE', '0', 'U')
        except Exception, err:
            print 'Something wrong while read disk info %s. err = '%dname + str(err)

### functions for rrdtool plotting ###
def getDSFromRRD(filename):
    info = rrdtool.info(filename)
    set = sets.Set()
    for tok in info.keys():
        m = re.match(r'ds\[(.+)\].+', tok)
        if m:

            set.add(m.group(1))
    return list(set)

def rrdGraphHeader(filename, period, title = '', vlabel = ''):
    global gWidth, gHeight
    cmdList = [filename, '--start', period,
            '--lower-limit', '0', '--vertical-label', vlabel,
            '--title', title, '-w', gWidth, '-h', gHeight,
            '--font', 'DEFAULT:11:', '--font', 'TITLE:13:']
    return cmdList

def plotCpuInfo(period):
    cmdList = rrdGraphHeader(cpuPNGFile%period, period, 'CPU Usage', '% of CPUs')
    # read DS from rrd and move idle to the back (for good looking STACK plot)
    ds_list = getDSFromRRD(cpuRRDFile)
    ds_list.append('idle')
    ds_list.remove('idle')
    colorReset()
    for i, ds in enumerate(ds_list):
        cmdList = cmdList +['DEF:%s=%s:%s:AVERAGE'%(ds,cpuRRDFile,ds),
            'CDEF:%s_scaled=%s,100,*'%(ds,ds),
            'AREA:%s_scaled%s:%s:STACK'%(ds,colorNext(),ds),
            'GPRINT:%s_scaled:MIN:Min\\:%%6.1lf%%%%'%ds,
            'GPRINT:%s_scaled:MAX:Max\\:%%6.1lf%%%%'%ds,
            'GPRINT:%s_scaled:AVERAGE:Avg\\:%%6.1lf%%%%'%ds,
            'COMMENT:\\n']

    rrdtool.graph(cmdList)

def plotCpuTempInfo(period):
    cmdList = rrdGraphHeader(cpuTempPNGFile%period, period, 'CPU Temp', 'Celsius')
    cmdList = cmdList + ['--lower-limit', '40', '--upper-limit', '70',
            'DEF:cpuTemp=%s:cpuTemp:AVERAGE'%cpuTempRRDFile,
            'AREA:cpuTemp%s:cpuTemp'%cBLUE,
            'GPRINT:cpuTemp:AVERAGE:Avg\\:%2.0lf',
            'GPRINT:cpuTemp:MAX:Max\\:%2.0lf',
            'GPRINT:cpuTemp:MIN:Min\\:%2.0lf']

    rrdtool.graph(cmdList)

def plotUptimeInfo(period):
    #uptime
    cmdList = rrdGraphHeader(uptimePNGFile%period, period, 'Uptime', 'minutes')
    cmdList = cmdList +['DEF:uptime=%s:uptime:LAST'%uptimeRRDFile,
        'LINE3:uptime%s'%cGREEN,
        'GPRINT:uptime:LAST:Uptime(minutes)\\:%4.0lf']

    rrdtool.graph(cmdList)

def plotPidsInfo(period):
    cmdList = rrdGraphHeader(pidsPNGFile, period, 'Numer of PIDs', 'number of PIDs')
    cmdList = cmdList + ['DEF:pids=%s:pids:AVERAGE'%pidsRRDFile ,
        'LINE3:pids%s'%cRED,
        'GPRINT:pids:MIN:Min\\:%4.0lf',
        'GPRINT:pids:MAX:Max\\:%4.0lf',
        'GPRINT:pids:AVERAGE:Avg\\:%4.1lf']

    rrdtool.graph(cmdList)

def plotMemoryInfo(period):
    cmdList = rrdGraphHeader(memPNGFile%period, period, 'Memory Usage', 'bytes')
    cmdList = cmdList + ['--base', '1024']
    colorReset()
    for i, ds in enumerate(getDSFromRRD(memRRDFile)):
        if ds.find('percent') > -1:
            continue
        cmdList = cmdList +['DEF:%s=%s:%s:AVERAGE'%(ds,memRRDFile,ds),
            'LINE3:%s%s:%s'%(ds,colorNext(),ds),
            'GPRINT:%s:MIN:Min\\:%%4.1lf %%Sbytes'%ds,
            'GPRINT:%s:MAX:Max\\:%%4.1lf %%Sbytes'%ds,
            'GPRINT:%s:AVERAGE:Avg\\:%%4.1lf %%Sbytes'%ds,
            'COMMENT:\\n']

    rrdtool.graph(cmdList)

#Mount Point UsedInfo
def plotMountUsageInfo(period):
    cmdList = rrdGraphHeader(mountUsagePNGFile%period, period, 'Mount Point Usage', 'bytes')
    cmdList = cmdList + ['--base', '1024']
    #prepare regexp for matching
    rexp = re.compile(os.path.split(mountRRDFile)[-1].replace('%s', r'(\w*)').replace('.',r'\.'))
    colorReset()
    for f in os.listdir(RRDSDIR):
        ma = re.match(rexp, f)
        if not ma:
            continue
        mp_name = ma.group(1)
        rrdfile = mountRRDFile%mp_name
        def_total = mp_name + 'total'
        def_used = mp_name + 'used'
        cmdList = cmdList +['DEF:%s=%s:%s:AVERAGE'%(def_total,rrdfile,'total'),
            'LINE1:%s%s:%s:dashes'%(def_total,colorNext(),'%s total\\:'%mp_name),
            'GPRINT:%s:MAX:%%4.1lf %%sbytes'%def_total,
            'COMMENT:\\n']

        cmdList = cmdList +['DEF:%s=%s:%s:AVERAGE'%(def_used,rrdfile,'used'),
            'LINE3:%s%s:%s'%(def_used,colorCurrent(),'%s used'%mp_name),
            'GPRINT:%s:MIN:Min\\:%%4.1lf %%Sbytes'%def_used,
            'GPRINT:%s:MAX:Max\\:%%4.1lf %%Sbytes'%def_used,
            'GPRINT:%s:AVERAGE:Avg\\:%%4.1lf %%Sbytes'%def_used,
            'COMMENT:\\n']

    rrdtool.graph(cmdList)

def plotDiskIOInfo (period):
    #prepare regexp for matching
    rexp = re.compile(os.path.split(diskRRDFile)[-1].replace('%s', r'(\w*)').replace('.',r'\.'))
    for f in os.listdir(RRDSDIR):
        ma = re.match(rexp, f)
        if not ma:
            continue
        disk_name = ma.group(1)
        rrdfile = diskRRDFile%disk_name
        cmdList = rrdGraphHeader(diskIOPNGFile%(disk_name, period), period, 'Disk %s IO Usage'%disk_name, 'bytes/s')
        cmdList = cmdList + ['--base', '1024']

        cmdList = cmdList +['DEF:%s=%s:%s:AVERAGE'%(disk_name + 'write_bytes',rrdfile,'write_bytes'),
            'LINE2:%s%s:%s'%(disk_name + 'write_bytes', cRED,'%s Input Rate'%disk_name),
            'GPRINT:%s:MIN:Min\\:%%4.1lf %%Sbytes/s'%(disk_name + 'write_bytes'),
            'GPRINT:%s:MAX:Max\\:%%4.1lf %%Sbytes/s'%(disk_name + 'write_bytes'),
            'GPRINT:%s:AVERAGE:Avg\\:%%4.1lf %%Sbytes/s'%(disk_name + 'write_bytes'),
            'COMMENT:\\n']

        cmdList = cmdList +['DEF:%s=%s:%s:AVERAGE'%(disk_name + 'read_bytes',rrdfile,'read_bytes'),
            'LINE2:%s%s:%s'%(disk_name + 'read_bytes', cGREEN,'%s Output Rate'%disk_name),
            'GPRINT:%s:MIN:Min\\:%%4.1lf %%Sbytes/s'%(disk_name + 'read_bytes'),
            'GPRINT:%s:MAX:Max\\:%%4.1lf %%Sbytes/s'%(disk_name + 'read_bytes'),
            'GPRINT:%s:AVERAGE:Avg\\:%%4.1lf %%Sbytes/s'%(disk_name + 'read_bytes'),
            'COMMENT:\\n']

        rrdtool.graph(cmdList)

def plotNetIOInfo(period):
    rexp = re.compile(os.path.split(netRRDFile)[-1].replace('%s', r'(\w*)').replace('.',r'\.'))
    for f in os.listdir(RRDSDIR):
        ma = re.match(rexp, f)
        if not ma:
            continue
        net_name = ma.group(1)
        rrdfile = netRRDFile%net_name
        cmdList = rrdGraphHeader(netPNGFile%(net_name, period), period, 'Net %s IO Usage'%net_name, 'bytes/s')
        cmdList = cmdList + ['--base', '1024']

        cmdList = cmdList +['DEF:%s=%s:%s:AVERAGE'%(net_name + 'bytes_recv',rrdfile,'bytes_recv'),
            'LINE2:%s%s:%s'%(net_name + 'bytes_recv', cRED,'%s Recieve Rate'%net_name),
            'GPRINT:%s:MIN:Min\\:%%4.1lf %%Sbytes/s'%(net_name + 'bytes_recv'),
            'GPRINT:%s:MAX:Max\\:%%4.1lf %%Sbytes/s'%(net_name + 'bytes_recv'),
            'GPRINT:%s:AVERAGE:Avg\\:%%4.1lf %%Sbytes/s'%(net_name + 'bytes_recv'),
            'COMMENT:\\n']

        cmdList = cmdList +['DEF:%s=%s:%s:AVERAGE'%(net_name + 'bytes_sent',rrdfile,'bytes_sent'),
                'LINE2:%s%s:%s'%(net_name + 'bytes_sent', cGREEN,'%s Send Rate'%net_name),
            'GPRINT:%s:MIN:Min\\:%%4.1lf %%Sbytes/s'%(net_name + 'bytes_sent'),
            'GPRINT:%s:MAX:Max\\:%%4.1lf %%Sbytes/s'%(net_name + 'bytes_sent'),
            'GPRINT:%s:AVERAGE:Avg\\:%%4.1lf %%Sbytes/s'%(net_name + 'bytes_sent'),
            'COMMENT:\\n']

        rrdtool.graph(cmdList)

### main functions ###
def get():
    try:
        getCpuInfo()
    except Exception, err:
        print "Can't collect cpuInfo data. Err = %s"%str(err)

    try:
        getCpuTempInfo()
    except Exception, err:
        print "Can't collect cpuTempInfo data. Err = %s"%str(err)

    try:
        getPidsInfo()
    except Exception, err:
        print "Can't collect pidsInfo data. Err = %s"%str(err)

    try:
        getUptimeInfo()
    except Exception, err:
        print "Can't collect uptimeInfo data. Err = %s"%str(err)

    try:
        getMemInfo()
    except Exception, err:
        print "Can't collect memInfo data. Err = %s"%str(err)

    try:
        getDiskInfo()
    except Exception, err:
        print "Can't collect diskInfo data. Err = %s"%str(err)

    try:
        getMountInfo()
    except Exception, err:
        print "Can't collect mountInfo data. Err = %s"%str(err)

    try:
        getNetInfo()
    except Exception, err:
        print "Can't collect netInfo data. Err = %s"%str(err)



def plot(*args):
    if len(args) < 1:
        usage()
        sys.exit(1)
    p = args[0]

    if not re.match('^-\d+[m,h,d,w]$', p):
        print 'period format error...'
        usage()
        sys.exit(1)

    try:
        plotCpuInfo(p)
    except Exception, err:
        print "Can't build cpuInfo plot. Err = %s"%str(err)

    try:
        plotCpuTempInfo(p)
    except Exception, err:
        print "Can't build cpuTempInfo plot. Err = %s"%str(err)

    try:
        plotUptimeInfo(p)
    except Exception, err:
        print "Can't build uptimeInfo plot. Err = %s"%str(err)

    try:
        plotPidsInfo(p)
    except Exception, err:
        print "Can't build pidsInfo plot. Err = %s"%str(err)

    try:
        plotMemoryInfo(p)
    except Exception, err:
        print "Can't build memoryInfo plot. Err = %s"%str(err)

    try:
        plotMountUsageInfo(p)

    except Exception, err:
        print "Can't build mountUsageInfo plot. Err = %s"%str(err)

    try:
        plotDiskIOInfo(p)
    except Exception, err:
        print "Can't build diskIOInfo plot. Err = %s"%str(err)

    try:
        plotNetIOInfo(p)
    except Exception, err:
        print "Can't build netIOInfo plot. Err = %s"%str(err)

def usage():
    print '''Usage:

    python rpi_monitor.py get

to create and collect data to rrds/*.rrd files. And

    python rpi_monitor.py plot period

to plot collected data. period is rrdtool format for time period (for example: daily plot -1d, weekly -1w, annual -1y).
    '''

def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'get':
        get()
    elif cmd == 'plot':
        plot(*sys.argv[2:])


if __name__ == '__main__':
    main()
