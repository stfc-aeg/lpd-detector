import optparse

class FemNodeList(object):

	def __init__(self):

		self.addrList = [ '192.168.0.17' , '192.168.0.102', '192.168.0.103',
						  '192.168.0.104', '192.168.0.105',  '192.168.0.106' ]
		self.nodeList = [ 1 ]
		self.port = 6969
		self.timeout = 5.0
						
		self.parser = optparse.OptionParser()
		self.parser.add_option("-i", "--ipaddr", dest="ipaddr", type="string", default=None,
						  help="override FEM host IP address")
		self.parser.add_option("-p", "--port", dest="port", type="int", default=None,
						  help="set FEM host port")
		self.parser.add_option("-n", "--node", dest="nodeList", type="int", action="append", default=None,
						  help="select FEM node")
		self.parser.add_option("-a", "--all", dest="all", action="store_true", default=False, 					      
					      help="Select all FEM nodes")
		self.parser.add_option("-t", "--timeout", dest="timeout", type="float", default=None,
						  help="set FEM transaction timeout")

	def parse_args(self):
			
		(options, args) = self.parser.parse_args()
					
		if options.port != None:
			self.port = options.port
			
		if options.timeout != None:
			self.timeout = options.timeout
		
		if options.nodeList != None:
			for node in options.nodeList:
				if node < 1 or node > len(self.addrList):
					self.parser.error('Illegal node %d specified' % node)
			self.nodeList = options.nodeList
		
		if options.all == True:
			self.nodeList = range(1, len(self.addrList)+1)

		if options.ipaddr != None:
			self.nodeList = [ 1 ]
			self.addrList = [ options.ipaddr ]

		return args
	
	def selected(self):

		for node in self.nodeList:
			yield (node, self.addrList[node - 1])
		
if __name__ == '__main__':

	theFems = FemNodeList()
	theFems.parse_args()
	
	for (node, addr) in theFems.selected():
		print node, addr