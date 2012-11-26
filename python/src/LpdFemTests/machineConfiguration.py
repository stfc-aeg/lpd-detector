'''
Created on 26 November 2012

@author: ckd27546
'''

# Import Python standard modules
import sys, os, string 
import socket


class machineConfiguration():
    

    # Dictionary of hostname -> 1g IP address
    one1gAddress = {'te7burntoak'  : '192.168.2.2',
                    'te7kiribati'  : '192.168.3.2',
                    'devgpu02'     : '192.168.3.2',}


    def set_10g_structs_variables_te2bank(self):
        """ Construct and return two dictionaries defining two network interfaces
        """
        
        x10g_0 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-01'),
                  'src_ip'  : self.ip_addr_to_uint32('192.168.7.2'),
                  'src_prt' : self.prt_addr_to_uint16('0000'),
                  # PC TARGET:
                  'dst_mac' : self.mac_addr_to_uint64('00-07-43-06-31-A3'),
                  'dst_ip'  : self.ip_addr_to_uint32('192.168.0.13'),
                  'dst_prt' : self.prt_addr_to_uint16('0000')}
        
        x10g_1 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-09'),
                  'src_ip'  : self.ip_addr_to_uint32('192.168.0.100'),
                  'src_prt' : self.prt_addr_to_uint16('0000'),
                  'dst_mac' : self.mac_addr_to_uint64('00-07-43-06-31-A3'),  # in vhdl 10g 
                  'dst_ip'  : self.ip_addr_to_uint32('192.168.0.13'),
                  'dst_prt' : self.prt_addr_to_uint16('0000')}
        return x10g_0, x10g_1

    def set_10g_structs_variables_te7burntoak(self):
        """ Construct and return two dictionaries defining two network interfaces
        """
        
        x10g_0 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-01'),
                  'src_ip'  : self.ip_addr_to_uint32('192.168.7.2'),
                  'src_prt' : self.prt_addr_to_uint16('8'),
                  # Target PC:
                  'dst_mac' : self.mac_addr_to_uint64('00-07-43-10-61-88'),
                  'dst_ip'  : self.ip_addr_to_uint32('192.168.7.1'),
                  'dst_prt' : self.prt_addr_to_uint16('61649')}
        
        x10g_1 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-01'),
                  'src_ip'  : self.ip_addr_to_uint32('192.168.8.2'),
                  'src_prt' : self.prt_addr_to_uint16('0000'),
                  'dst_mac' : self.mac_addr_to_uint64('00-07-43-06-31-A3'),  # in vhdl 10g 
                  'dst_ip'  : self.ip_addr_to_uint32('192.168.8.1'),
                  'dst_prt' : self.prt_addr_to_uint16('0000')}
    
        return x10g_0, x10g_1
    
    def set_10g_structs_variables_devgpu02(self):
        """ Construct and return two dictionaries defining two network interfaces
        """
        
        x10g_0 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-01'),
                  'src_ip'  : self.ip_addr_to_uint32('10.0.0.2'),            # Updated
                  'src_prt' : self.prt_addr_to_uint16('8'),
                  # Target PC:
                  'dst_mac' : self.mac_addr_to_uint64('00-07-43-10-65-A0'),    # Updated
                  'dst_ip'  : self.ip_addr_to_uint32('10.0.0.1'),            # Updated
                  'dst_prt' : self.prt_addr_to_uint16('61649')}
        
        x10g_1 = {'src_mac' : self.mac_addr_to_uint64('62-00-00-00-00-01'),
                  'src_ip'  : self.ip_addr_to_uint32('192.168.8.2'),
                  'src_prt' : self.prt_addr_to_uint16('0000'),
                  'dst_mac' : self.mac_addr_to_uint64('00-07-43-06-31-A3'),  # in vhdl 10g 
                  'dst_ip'  : self.ip_addr_to_uint32('192.168.8.1'),
                  'dst_prt' : self.prt_addr_to_uint16('0000')}
    
        return x10g_0, x10g_1


    def mac_addr_to_uint64(self, mac_addr_str):
        """ convert hex MAC address 'u-v-w-x-y-z' string to integer """
        # Convert MAC address into list of 6 elements (and removing the - characters)
        mac_addr_list = mac_addr_str.split('-')   
        # Convert hexadecimal values into the decimals
        mac_addr_list = [int(val, 16) for val in mac_addr_list]
        # combine the 6 elements into a single 48 bit MAC value
        mac_address = 0
        mac_address = (mac_address | mac_addr_list[0])
        mac_address = (mac_address | (mac_addr_list[1] << 8))
        mac_address = (mac_address | (mac_addr_list[2] << 16))
        mac_address = (mac_address | (mac_addr_list[3] << 24))
        mac_address = (mac_address | (mac_addr_list[4] << 32))
        mac_address = (mac_address | (mac_addr_list[5] << 40))
        return mac_address
    
    def ip_addr_to_uint32(self, ip_addr_str):
        # Convert IP address into list of 4 elements (and removing the - characters)
        ip_addr_list = ip_addr_str.split('.') 
        # Convert hexadecimal values into the decimals
        ip_addr_list = [int(val) for val in ip_addr_list]    
        # combine the 4 elements into a single 32 bit value 
        ip_address = 0
        ip_address = (ip_address | ip_addr_list[0])
        ip_address = (ip_address | (ip_addr_list[1] << 8))
        ip_address = (ip_address | (ip_addr_list[2] << 16))
        ip_address = (ip_address | (ip_addr_list[3] << 24))
        return ip_address 


    def uint32_to_ip_addr(self, ip_addr):
        # Construct IP address as a string from a uint32 integer
        ip_list =[ ]
        ip_address = (ip_addr & 0xFF000000) >> 24
        ip_list.append(  str(ip_address) )
        ip_address = (ip_addr & 0xFF0000) >> 16
        ip_list.append(  str(ip_address) )
        ip_address = (ip_addr & 0xFF00) >> 8
        ip_list.append(  str(ip_address) )
        ip_address = (ip_addr & 0xFF)
        ip_list.append(  str(ip_address) )
        # Add the list in reverse order into one string
        ip_addr_str = ""
        for idx in range( 4-1, -1, -1):
            ip_addr_str += ip_list[idx] + "."
        return ip_addr_str[0:-1]





    def prt_addr_to_uint16(self, prt_addr_str):
        #convert hex prt string to integer
        return int(prt_addr_str)
        

    def getStructsVariables(self):
        '''
            Depending on which machine the request comes from, return the values for the corresponding set_10g_structs_variables_XXX() function
        '''
        
        return self.x10g_0, self.x10g_1
    
    def get10gDestinationIpAddress(self, aInterfaceNumber):
        '''
            Depending on which machine the request came from, return target PC IP address for 10G interface
        '''
#        print "aInterfaceNumber: ", aInterfaceNumber
        ip = 0
        if aInterfaceNumber == 0:
            ip = self.uint32_to_ip_addr( self.x10g_0['dst_ip'] )
        elif aInterfaceNumber == 1:
            ip = self.uint32_to_ip_addr( self.x10g_1['dst_ip'] )
        else:
            ip = None
        return ip
    
    def __init__(self):
        '''
            Initialise the class by determining which PC it is the run on
        '''

        # Determine name of current machine
        fullDomainName = socket.gethostname()
        # Only need hostname, not domain part
        hostName = fullDomainName.partition('.')[0]
        
        self.hostname = hostName

        # Construct function name to be called from self.hostname
        try:
            handlerMethod = getattr(self, "set_10g_structs_variables_%s" % self.hostname)
        except Exception as e:
            print "No network information defined for this machine: ", self.hostname
            print "\tError: ", e, "\nExiting.."
            return None, None
        
        # Generate interface dictionaries for 10G interfaces
        self.x10g_0, self.x10g_1 = handlerMethod()
        
    def determineOneGigIP(self):
        '''
            Return IP address for the 1g network card
        '''

        return self.one1gAddress[self.hostname]
        