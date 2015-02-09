#!/usr/bin/env python
import sys, re, os, sets
import rrdtool

RUNDIR = os.path.dirname(os.path.realpath(__file__))
RRDSDIR = os.path.join(RUNDIR, 'rrds')
REPORTDIR = os.path.join(RUNDIR, 'report')
cpuRRDFile = os.path.join(RRDSDIR, 'cpustatus.rrd')
memRRDFile = os.path.join(RRDSDIR, 'meminfo.rrd')
uptimeRRDFile = os.path.join(RRDSDIR, 'uptime.rrd')
mountRRDFile = os.path.join(RRDSDIR, 'mount-%s.rrd')
netRRDFile = os.path.join(RRDSDIR, 'interface-%s.rrd')
cpuTempRRDFile = os.path.join(RRDSDIR, 'cputemp.rrd')
pidsRRDFile = os.path.join(RRDSDIR, 'pids.rrd')
diskRRDFile = os.path.join(RRDSDIR, 'hdd-%s.rrd')



memPNGFile = os.path.join(REPORTDIR, 'meminfo%s.png')
uptimePNGFile = os.path.join(REPORTDIR, 'uptime%s.png')
mountUsagePNGFile = os.path.join(REPORTDIR, 'mountusage%s.png')
netPNGFile = os.path.join(REPORTDIR, 'interface-%s%s.png')
diskIOPNGFile = os.path.join(REPORTDIR, 'hddio-%s%s.png')
cpuTempPNGFile = os.path.join(REPORTDIR, 'cputemp%s.png')
cpuPNGFile = os.path.join(REPORTDIR, 'cpuusage%s.png')
pidsPNGFile = os.path.join(REPORTDIR, 'pids.png')

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

gWidth='600'
gHeight='200'

def getDSFromRRD(filename):
    info = rrdtool.info(filename)
    set = sets.Set()
    for tok in info.keys():
        m = re.match(r'ds\[(.+)\].+', tok)
        if m:

            set.add(m.group(1))
    return list(set)

    #Temp
#    rrdtool.graph(REPORTDIR + '/cpuTemp' + period + '.png', '--start', period,
#        '--title', 'CPU Temperature', '-w', gWidth, '-h', gHeight,
#        '--lower-limit', '40', '--upper-limit', '70',
#        'DEF:ctemp=' + cpuRRDFile + ':cpuTemp:AVERAGE',
#        'LINE1:ctemp' + cRED,
#        'GPRINT:ctemp:AVERAGE:Avg\\:%2.0lf',
#        'GPRINT:ctemp:MAX:Max\\:%2.0lf',
#        'GPRINT:ctemp:MIN:Min\\:%2.0lf',
#        'COMMENT:\\n')
#
#    #Usage
#    rrdtool.graph(REPORTDIR + '/cpuUsage' + period + '.png', '--start', period,
#        '--title', 'CPU Usage (%)', '-w', gWidth, '-h', gHeight,
#        '--lower-limit', '0', '--upper-limit', '100',
#        'DEF:cusage=' + cpuRRDFile + ':cpuUsage:AVERAGE',
#        'AREA:cusage' + cGREEN,
#        'GPRINT:cusage:AVERAGE:Avg\\:%2.0lf',
#        'COMMENT:\\n')
#
#    #PID
#    rrdtool.graph(REPORTDIR + '/PIDs' + period + '.png', '--start', period,
#        '--title', 'PIDs', '-w', gWidth, '-h', gHeight,
#        '--lower-limit', '40',
#        'DEF:cpid=' + cpuRRDFile + ':pids:AVERAGE',
#        'LINE1:cpid' + cBLUE,
#        'COMMENT: ',
#        'GPRINT:cpid:AVERAGE:Avg\\:%2.0lf',
#        'GPRINT:cpid:MAX:Max\\:%2.0lf',
#        'GPRINT:cpid:MIN:Min\\:%2.0lf',
#        'COMMENT:\\n')

def rrdGraphHeader(filename, period, title = '', vlabel = ''):
    global gWidth, gHeight
    cmdList = [filename, '--start', period,
            '--lower-limit', '0', '--vertical-label', vlabel,
            '--title', title, '-w', gWidth, '-h', gHeight,
            '--font', 'DEFAULT:11:', '--font', 'TITLE:13:']
    return cmdList

def cpuInfo(period):
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

def cpuTempInfo(period):
    cmdList = rrdGraphHeader(cpuTempPNGFile%period, period, 'CPU Temp', 'Celsius')
    cmdList = cmdList + ['--lower-limit', '40', '--upper-limit', '70',
            'DEF:cpuTemp=%s:cpuTemp:AVERAGE'%cpuTempRRDFile,
            'AREA:cpuTemp%s:cpuTemp'%cBLUE,
            'GPRINT:cpuTemp:AVERAGE:Avg\\:%2.0lf',
            'GPRINT:cpuTemp:MAX:Max\\:%2.0lf',
            'GPRINT:cpuTemp:MIN:Min\\:%2.0lf']

    rrdtool.graph(cmdList)

def uptimeInfo(period):
    #uptime
    cmdList = rrdGraphHeader(uptimePNGFile%period, period, 'Uptime', 'minutes')
    cmdList = cmdList +['DEF:uptime=%s:uptime:LAST'%uptimeRRDFile,
        'LINE3:uptime%s'%cGREEN,
        'GPRINT:uptime:LAST:Uptime(minutes)\\:%4.0lf']

    rrdtool.graph(cmdList)

def pidsInfo(period):
    cmdList = rrdGraphHeader(pidsPNGFile, period, 'Numer of PIDs', 'number of PIDs')
    cmdList = cmdList + ['DEF:pids=%s:pids:AVERAGE'%pidsRRDFile ,
        'LINE3:pids%s'%cRED,
        'GPRINT:pids:MIN:Min\\:%4.0lf',
        'GPRINT:pids:MAX:Max\\:%4.0lf',
        'GPRINT:pids:AVERAGE:Avg\\:%4.1lf']

    rrdtool.graph(cmdList)

def memoryInfo(period):
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
def mountUsageInfo(period):
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

def diskIOInfo (period):
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

def netIOInfo(period):
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

def usage():
    print "usage"

def main():

    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    p = sys.argv[1]

    if not re.match('^-\d+[m,h,d,w]$', p):
        print 'formate Error...'
        sys.exit(1)

    try:
        cpuInfo(p)
    except Exception, err:
        print "Can't build cpuInfo plot. Err = %s"%str(err)

    try:
        cpuTempInfo(p)
    except Exception, err:
        print "Can't build cpuTempInfo plot. Err = %s"%str(err)

    try:
        uptimeInfo(p)
    except Exception, err:
        print "Can't build uptimeInfo plot. Err = %s"%str(err)

    try:
        pidsInfo(p)
    except Exception, err:
        print "Can't build pidsInfo plot. Err = %s"%str(err)

    try:
        memoryInfo(p)
    except Exception, err:
        print "Can't build memoryInfo plot. Err = %s"%str(err)

    try:
        mountUsageInfo(p)

    except Exception, err:
        print "Can't build mountUsageInfo plot. Err = %s"%str(err)

    try:
        diskIOInfo(p)
    except Exception, err:
        print "Can't build diskIOInfo plot. Err = %s"%str(err)

    try:
        netIOInfo(p)
    except Exception, err:
        print "Can't build netIOInfo plot. Err = %s"%str(err)


if __name__ == '__main__':
    main()

