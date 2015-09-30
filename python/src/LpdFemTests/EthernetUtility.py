'''
    EthernetUtility.py - Some tool(s) for obtaining Ethernet card information
'''

import os, re

class EthernetUtility():
    
    def __init__(self, ethernetNumber="eth0"):
        
        self.macAddress = ""
        self.ipAddress  = ""
        
        self.ethernetInterface = os.popen("/sbin/ifconfig %s" % ethernetNumber)
        #print "2"
        try:
            for line in self.ethernetInterface.readlines():
                if 'HWaddr' in line:
                    self.macLine = line
                    #print "'HWaddr': ", line
                if 'inet addr:' in line:
                    self.ipLine = line
                    #print "'inet addr':", line
        except Exception as e:
            print "EthernetUtility error: ", e
        #print "3"
        self.ethernetInterface.close()
        
        # If ethernetNumber's card doesn't exist, and uncatchable error thrown between "2" and "3"..!
    
    def macAddressGet(self):
        '''
            Get MAC Address (from ifconfig command)
        '''

        self.macAddress = None        
        try:
            self.macAddress = re.compile(r'HWaddr (\w+\:\w+\:\w+\:\w+\:\w+\:\w+)').search(self.macLine).group(1)
        except IOError,(errno, strerror):
            print "MAC Address IO Error(%s): %s" % (errno, strerror)
        except AttributeError:
            print "Error extracting MAC address"
        else:
            # Replace ':' in MAC address with '-'
            self.macAddress = self.macAddress.replace(":", "-")
            
        return self.macAddress
    
    def ipAddressGet(self):
        '''
            Get IP Address (from ifconfig command)
        '''
        self.ipAddress = None
        try:
            self.ipAddress = re.compile(r'inet addr:(\d+\.\d+\.\d+\.\d+)').search(self.ipLine).group(1)
        except AttributeError:
            print "EthernetUtility: Unable to extract IP address"
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
        (ipEnding, destAddress) = (None, None)
        try:
            ipEnding = int(ipList[3])
        except Exception as e:
            print "obtainAddressEnding Error: ", e
        if ipEnding is None:
            # try statement returned blank
            pass
        else:
            #print "IP: ", ip, "ipList: ", ipList, "ipEnding: ", ipEnding, "\n"
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
    