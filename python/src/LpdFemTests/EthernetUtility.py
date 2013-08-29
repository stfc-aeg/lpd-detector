'''
    EthernetUtility.py - Some tool(s) for obtaining Ethernet card information
'''

import os, re

class EthernetUtility():
    
    def __init__(self, ethernetNumber="eth0"):
        
        self.macAddress = ""
        self.ipAddress  = ""
        
        self.ethernerNumber = ethernetNumber
        self.ethernetInterface = os.popen("/sbin/ifconfig %s" % ethernetNumber)
        
        for line in self.ethernetInterface.readlines():
            if 'HWaddr' in line:
                self.macLine = line
            if 'inet addr:' in line:
                self.ipLine = line

        self.ethernetInterface.close()
    
    def macAddressGet(self):
        '''
            Get MAC Address (from ifconfig command)
        '''
        
        try:
            self.macAddress = re.compile(r'HWaddr (\w+\:\w+\:\w+\:\w+\:\w+\:\w+)').search(self.macLine).group(1)
        except IOError,(errno, strerror):
            print "MAC Address IO Error(%s): %s" % (errno, strerror)

        # Replace ':' in MAC address with '-'
        self.macAddress = self.macAddress.replace(":", "-")
            
        return self.macAddress
    
    def ipAddressGet(self):
        '''
            Get IP Address (from ifconfig command)
        '''

        try:
            self.ipAddress = re.compile(r'inet addr:(\d+\.\d+\.\d+\.\d+)').search(self.ipLine).group(1)
        except AttributeError:
            print "EthernetUtility: Unable to extract IP address; is FEM powered up?"
        except IOError,(errno, strerror):
            print "IP Address IO Error(%s): %s" % (errno, strerror)
        
        return self.ipAddress
    
    def obtainDestIpAddress(self, ip):
        '''
            Helper function: Get Destination address assuming it's .2 in whatever
            IP address (network )that the Source address is residing in.
            eg: If Source IP: 10.0.0.1, Destination IP: 10.0.0.2
        '''
        
        ipList = ip.split(".")
        try:
            ipEnding = int(ipList[3])
        except Exception as e:
            print "obtainAddressEnding Error: ", e
        # Increment, eg 10.0.0.1 => 10.0.0.2
        ipList[3] = ipEnding + 1
        # Turn into string
        ipStr = ipList.__str__()
        # String format: "['10', '0', '0', '1']". Replace "," with "." and  remove unwanted characters, eg: ' [ ]
        destAddress = ipStr.replace(", ", ".").replace("'", "").replace("[", "").replace("]", "")

        return destAddress
        
        
if __name__ == '__main__':
    
    ethCard = EthernetUtility("eth1")
    
    print "In ethernet interface: %s" % ethCard.ethernerNumber
    mac     = ethCard.macAddressGet()
    srcIp   = ethCard.ipAddressGet()
    dstIp   = ethCard.obtainDestIpAddress(srcIp)
    print "Src MAC: %r (%r)" % (mac, type(mac)) 
    print "Src IP:  %r (%r)" % (srcIp,  type(srcIp))
    print "Dst IP:  %r (%r)" % (dstIp,  type(dstIp))
    