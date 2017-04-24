'''
Created on Mar 20, 2017

@author: tcn45
'''
from excalibur import ExcaliburClient
import logging

def main():
    
    client = ExcaliburClient(log_level=logging.DEBUG)
    
    client.print_all()
    

if __name__ == '__main__':
    
    main()