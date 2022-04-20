#!/usr/bin/env python

# Script name: Arista-L4-healthcheck.py
# Script purpose: 
#       This script performs an OSI L4 monitor of one or more services, takes individual action
#       on a service in the event of failure, and takes action to failback to normal state.
# 
# Intellectional Property Statement
# Copyright (c) 2022
# Nomadic IT LLC
# Author: Steve Troxel <steve.troxel@nomadicit.com>
# License: Apache License, Version 2.0
# 
# Description:
# This script has a main loop that runs through all defined services to monitor,
# and each defined service has its own loop in the event of a connection failure.
# On an Arista switch, the failscript and failbackscript define a command alias
# that should be applied to the EOS configuration.

from re import I
import time, syslog, subprocess, socket
# Declare values for the variables that define how the script will monitor the services
# Timeout defines in seconds how long an connection will be attempted before the script ends its attempt
timeout = 5
# Retry defines how many times the script will attempt a L4 TCP connection in the event of a failed attempt
retry = 3
# Delay defines in seconds how long the script will wait before attempting to make another connection after a failed attempt
delay = 5
# Loopinterval defines in seconds how long the script will wait before starting the main loop after completing an iteration
loopinterval = 5
# Testmode is a boolean value that is used to test the scripts functioning prior to production deployment as an event handler.
# It produces console text in lieu of taking any action, and is therefore a passive test of failover and failback.
testmode = True


def Main():
# Create an independent line to describe each service to be monitored. The IP can be either an FQDN or an IP.
# Each line in the info list but the last should end in a comma. This is because the info list is a list of dictionaries.
    checkList=[
                {'serviceName': 'Google', 'host': 'www.google.com', 'port': '80', 'failscript': 'Google-failure', 'failbackscript': 'Google-failback'}, 
                {'serviceName': 'Bing', 'host': 'www.bing.com', 'port': '80', 'failscript': 'Bing-failure', 'failbackscript': 'Bing-failback'}, 
                {'serviceName': 'Yahoo', 'host': 'www.yahoo.com', 'port': '80', 'failscript': 'Yahoo-failure', 'failbackscript': 'Yahoo-failback'}, 
                {'serviceName': 'DNS', 'host': '1.1.1.1', 'port': '53', 'failscript': 'DNS-failure', 'failbackscript': 'DNS-failback'}
        ]
# The failed list is populated by failed attempts. This provides state information to the script between loop runs.
    failed = []

    while True:
        for host in checkList:
            serviceCheck = host['serviceName']
            hostCheck = host['host']
            portCheck = host['port']
# Actions when the port check succeeds
            if checkHost(hostCheck, portCheck):
# First check to see if this check has failed before
                if host['host'] in failed:
# If it has it will be in the failed list.
# First, remove it from the failed list and then run the failback script. Create syslog entries.
                        failed.remove(host['host'])
                        if testmode:
                                print ('The host at %s for %s is REACHABLE again and will be executing config change.'% (hostCheck, serviceCheck))
                                ()
                        else:
                                subprocess.check_output('sudo ip netns exec default FastCli -p 15 -c %s' % host['failbackscript'],shell=True)
                                syslog.openlog('IP SLA', 0, syslog.LOG_LOCAL4 )
                                syslog.syslog('IP-SLA-9-CHANGE: %s:%s host once again available. Adding PBR for %s.' % (hostCheck,portCheck, serviceCheck))
                                ()
                else:
# If it succeeds and it wasn't in the failed list, do nothing
                        if testmode: print ('The host at %s for %s is REACHABLE.'% (hostCheck, serviceCheck)) 
                        ()
            else:
# Actions when the port check fails. First check if it is in failed dictionary.
                if host['host'] in failed:
# If it fails and it was in the failed list, do nothing
                        if testmode:
                                print ('The host at %s for %s has FAILED again.'% (hostCheck, serviceCheck))
                                ()
                        else:
                                ()
                else:
                        ()
# If it wasn't in the failed list, add it.
                        failed.append(host['host'])
# Execute the failback script and log the failure. 
                        if testmode:
                                print ('The host at %s for %s has FAILED. Executing config change.'% (hostCheck, serviceCheck))
                                ()
                        else:
                                subprocess.check_output('sudo ip netns exec default FastCli -p 15 -c %s' % host['failscript'],shell=True)
                                syslog.openlog('IP SLA', 0, syslog.LOG_LOCAL4 )
                                syslog.syslog('IP-SLA-9-CHANGE: %s:%s host reachability failure. Removing PBR for %s.' % (hostCheck,portCheck,serviceCheck))
                                ()
        print ('Going to sleep for ' + str(loopinterval) + ' seconds before looping though the hosts again.')
        time.sleep(loopinterval)
        ()

def isOpen(ip, port):
    socketSession = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketSession.settimeout(timeout)
    try:
            socketSession.connect((ip, int(port)))
            socketSession.shutdown(socket.SHUT_RDWR)
            if testmode: print ('Attempting to connect to %s for up to %s seconds.' % (ip, str(timeout)))
            return True
            ()
    except:
            return False
            ()
    finally:
            socketSession.close()
            ()
def checkHost(host, port):
#   The checkHost function calls the isOpen function. The range class is instantiated to define the number of times to retry
#   the checkHost function before aborting.
    if testmode: print('Getting started with the checkHost function on %s on TCP port %s.' % (host, port))
    hostUp = False
    for i in range(retry):
            if testmode: print ('Try #' + str(i+1) + ' in the ' + str(retry) + ' attempts I will make in this loop.')
            if isOpen(host, port):
                    hostUp = True
                    if testmode: print ('The host ' + host + ' does appear to be up.')
                    break
            else:
                    if testmode: print ('The host ' + host + ' is not responding yet.')
                    time.sleep(delay)
                    ()
    return hostUp
    ()

if __name__ == '__main__':
   Main()
   ()