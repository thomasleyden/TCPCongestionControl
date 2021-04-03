#!/usr/bin/env python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.util import quietRun, dumpNodeConnections
from mininet.cli import CLI
import os
import subprocess
import time
from os import path

class Dumbbell_Topology(Topo):
	# Dumbbell topology for mininet

	def build(self, delay=21):
		""" 
		For all calculations, we assume 12000 bits/packet and 1500-byte packets
		"""

		# Backbone Router 1
		s1 = self.addSwitch('s1')
		# Backbone Router 2
		s2 = self.addSwitch('s2')
		# Access Router 1
		s3 = self.addSwitch('s3')
		# Access Router 2
		s4 = self.addSwitch('s4')
		
		"""
		The backbone routers can transmit at 984Mbps (82p/ms).
		Bandwidth of 984Mbps.
		"""
		# Bandwidth is in Mbps, delay is in ms, and max queue size is in packets
		# Connect Backbone Router 1 to Backbone Router 2
		self.addLink(s1, s2, bw=984, delay='{0}ms'.format(delay))
		
		"""
		The access routers can transmit/receive at 252Mbps (21p/ms).
		Bandwidth of 252Mbps and a delay of 0ms.
		Max queue size = 20% * bandwidth * delay.
		"""
		# Bandwidth is in Mbps, delay is in ms, and max queue size is in packets
		# Connect Access Router 1 to Backbone Router 1
		self.addLink(s1, s3, bw=252, delay='0ms', max_queue_size=21*delay*0.2)
		# Connect Access Router 2 to Backbone Router 2
		self.addLink(s2, s4, bw=252, delay='0ms', max_queue_size=21*delay*0.2)
		
		# Source 1
		h1 = self.addHost('h1')
		# Source 2
		h2 = self.addHost('h2')
		# Receiver 1
		h3 = self.addHost('h3')
		# Receiver 2
		h4 = self.addHost('h4')
		
		"""
		The hosts can transmit/receive at 960Mbps (80p/ms).
		Delay of 0ms.
		"""
		# Bandwidth is in Mbps, delay is in ms, and max queue size is in packets
		# Connect Source 1 to Access Router 1
		self.addLink(h1, s3, bw=960, delay='0ms')
		# Connect Source 2 to Access Router 1
		self.addLink(h2, s3, bw=960, delay='0ms')
		# Connect Receiver 1 to Access Router 2
		self.addLink(h3, s4, bw=960, delay='0ms')
		# Connect Receiver 2 to Access Router 2
		self.addLink(h4, s4, bw=960, delay='0ms')
	
def run_tcp_tests_cwnd(algorithm, delay):
	topo = Dumbbell_Topology(delay)
	net = Mininet(topo=topo, link=TCLink)
	net.start()
	
	print("Dumping host connections")
	dumpNodeConnections(net.hosts)
	
	#CLI(net)
	
	h1, h2, h3, h4 = net.getNodeByName('h1', 'h2', 'h3', 'h4')
	host_addr = dict({'h1': h1.IP(), 'h2': h2.IP(), 'h3': h3.IP(), 'h4': h4.IP()})
	print('Host addresses: {0}'.format(host_addr))
	
	if (path.exists('cwnd_{0}_{1}_{2}'.format(algorithm, h1, delay))):
		os.remove('cwnd_{0}_{1}_{2}'.format(algorithm, h1, delay))
	if (path.exists('cwnd_{0}_{1}_{2}'.format(algorithm, h2, delay))):
		os.remove('cwnd_{0}_{1}_{2}'.format(algorithm, h2, delay))
	
	h1_runtime = 100
	stagger_delay = 50
	h2_runtime = 50
	
	# run iperf
	popens = dict()
	print('Starting iperf server h3')
	popens[h3] = h3.popen('iperf3 -s -p 5566 -1', shell=True)
	print('Starting iperf server h4')
	popens[h4] = h4.popen('iperf3 -s -p 5566 -1', shell=True)
	time.sleep(5)
	
	print('Starting iperf client h1')
	popens[h1] = h1.popen('nohup iperf3 -c {0} -p 5566 -t {1} -C {2} -i 1 > results/cwnd_{3}_h1_{4}.txt'.format(h3.IP(), h1_runtime, algorithm, algorithm, delay), shell=True)

	print("Waiting to stagger h1 start")
	for i in range(0, stagger_delay):
		time.sleep(1)
		if i % 20 == 0:
			print("Sleep")

	print("Starting iperf client h2")
	popens[h2] = h2.popen('nohup iperf3 -c {0} -p 5566 -t {1} -C {2} -i 1 > results/cwnd_{3}_h2_{4}.txt'.format(h4.IP(), h2_runtime, algorithm, algorithm, delay), shell=True)

	print("Waiting for iperf to finish")
	for i in range(0, h2_runtime):
		time.sleep(1)
		if i % 20 == 0:
			print("Sleep")

	time.sleep(5)

	popens[h1].terminate()
	popens[h2].terminate()
	popens[h3].terminate()
	popens[h4].terminate()
	
	print("Stopping test")
	net.stop()
	
	print("Processing data")
	#gather_data(algorithm, delay, True)
	#plot_iperf(algorithm, delay, True)

def clean_environment():
	print("Cleaning mininet")
	clean1 = subprocess.Popen("sudo mn -c", shell=True)
	clean1.wait()
	print("Cleaning Iperf")
	clean2 = subprocess.Popen("sudo pkill -9 iperf", shell=True)
	clean2.wait()
	
if __name__ == '__main__':
	delay = [21, 81, 162]
	algorithm = ['cubic', 'reno', 'westwood', 'vegas']

	delay = [21]
	
	setLogLevel('info')
	
	clean_environment()
	
	for x in algorithm:
		for y in delay:
			clean_environment()
			print("CWND for {0} {1}".format(x, y))
			run_tcp_tests_cwnd(x, y)
	

