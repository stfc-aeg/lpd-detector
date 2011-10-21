'''
Created on Sep 23, 2011

@author: tcn45
'''
from FemApi.FemTransaction import FemTransaction
from FemClient.FemClient import FemClient

host = '127.0.0.1'
port = 5000

theFem = FemClient((host, port))
response = theFem.commandSend(0x1004)
print response

theFem.close()
