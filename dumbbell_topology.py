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

	def build(self, delay=2):
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

	
def run_tests():
	topo = Dumbbell_Topology(delay=21)
	net = Mininet(topo=topo, link=TCLink)
	net.start()
	
	print("Dumping host connections")
	dumpNodeConnections(net.hosts)
	
	print("Testing network connectivity")
	h1, h3 = net.get('h1', 'h3')
	h2, h4 = net.get('h2', 'h4')
	
	for i in range(1, 10):
		net.pingFull(hosts=(h1, h3))
	
	for i in range(1, 10):
		net.pingFull(hosts=(h3, h1))
		
	for i in range(1, 10):
		net.pingFull(hosts=(h2, h4))
	
	for i in range(1, 10):
		net.pingFull(hosts=(h4, h2))
		
	print("Testing bandwidth between h1 and h3..")
	net.iperf(hosts=(h1, h3), fmt='m', seconds=10, port=5001)
	
	print("Testing bandwidth between h2 and h4")
	net.iperf(hosts=(h2, h4), fmt='m', seconds=10, port=5001)
	
	print("Stopping test...")
	net.stop()

	
def run_tcp_tests_cwnd(algorithm, delay):
	topo = Dumbbell_Topology(delay)
	net = Mininet(topo=topo, link=TCLink)
	net.start()
	#CLI(net)
	
	h1, h2, h3, h4 = net.getNodeByName('h1', 'h2', 'h3', 'h4')
	host_addr = dict({'h1': h1.IP(), 'h2': h2.IP(), 'h3': h3.IP(), 'h4': h4.IP()})
	print('Host addresses: {0}'.format(host_addr))
	
	if (path.exists('cwnd_{0}_{1}_{2}'.format(algorithm, h1, delay))):
		os.remove('cwnd_{0}_{1}_{2}'.format(algorithm, h1, delay))
	if (path.exists('cwnd_{0}_{1}_{2}'.format(algorithm, h2, delay))):
		os.remove('cwnd_{0}_{1}_{2}'.format(algorithm, h2, delay))
	
	# run iperf
	popens = dict()
	print('Starting iperf server h3')
	popens[h3] = h3.popen('iperf3 -s -p 5566 -1', shell=True)
	print('Starting iperf server h4')
	popens[h4] = h4.popen('iperf3 -s -p 5566 -1', shell=True)
	time.sleep(5)
	
	print('Starting iperf client h1')
	popens[h1] = h1.popen('iperf3 -c {0} -p 5566 -t 200 -C {1} -i 1 > cwnd_{2}_{3}_{4}'.format(h3.IP(), algorithm, algorithm, h1, delay), shell=True)
	print('200 delay for client h2')
	for i in range(40,0,-1):
		time.sleep(1)
		print(i)
	print('Starting iperf client h2')
	popens[h2] = h2.popen('iperf3 -c {0} -p 5566 -t 160 -C {1} -i 1 > cwnd_{2}_{3}_{4}'.format(h4.IP(), algorithm, algorithm, h2, delay), shell=True)

	print("Waiting for clients to finish...")
	
	try:
		popens[h1].communicate(timeout=200)
	except subprocess.TimeoutExpired as e:
		popens[h1].kill()
	try:
		popens[h2].communicate(timeout=200)
	except subprocess.TimeoutExpired as e:
		popens[h2].kill()
	popens[h3].terminate()
	popens[h4].terminate()
	
	print("Stopping test")
	net.stop()
	
	print("Processing data")
	gather_data(algorithm, delay, True)
	plot_iperf(algorithm, delay, True)


def run_tcp_tests_fairness(algorithm, delay):
	topo = Dumbbell_Topology(delay)
	net = Mininet(topo=topo)
	net.start()
	#CLI(net)
	
	h1, h2, h3, h4 = net.getNodeByName('h1', 'h2', 'h3', 'h4')
	host_addr = dict({'h1': h1.IP(), 'h2': h2.IP(), 'h3': h3.IP(), 'h4': h4.IP()})
	print('Host addresses: {0}'.format(host_addr))
	
	if (path.exists('fair_{0}_{1}_{2}'.format(algorithm, h3, delay))):
		os.remove('fair_{0}_{1}_{2}'.format(algorithm, h3, delay))
	if (path.exists('fair_{0}_{1}_{2}'.format(algorithm, h4, delay))):
		os.remove('fair_{0}_{1}_{2}'.format(algorithm, h4, delay))
	
	# run iperf
	popens = dict()
	print('Starting iperf server h3')
	popens[h3] = h3.popen('iperf3 -s -p 5566 -i 1 -1 > fair_{0}_{1}_{2}'.format(algorithm, h3, delay), shell=True)
	print('Starting iperf server h4')
	popens[h4] = h4.popen('iperf3 -s -p 5566 -i 1 -1 > fair_{0}_{1}_{2}'.format(algorithm, h4, delay), shell=True)
	time.sleep(5)
	
	print('Starting iperf client h1')
	popens[h1] = h1.popen('iperf3 -c {0} -p 5566 -t 100 -C {1}'.format(h3.IP(), algorithm), shell=True)
	print('Starting iperf client h2')
	popens[h2] = h2.popen('iperf3 -c {0} -p 5566 -t 100 -C {1}'.format(h4.IP(), algorithm), shell=True)
	
	print("Waiting for clients to finish...")
		
	try:
		popens[h1].communicate(timeout=100)
	except subprocess.TimeoutExpired as e:
		popens[h1].kill()
	try:
		popens[h2].communicate(timeout=100)
	except subprocess.TimeoutExpired as e:
		popens[h2].kill()
	popens[h3].terminate()
	popens[h4].terminate()
	
	print("Stopping test")
	net.stop()
	
	print("Processing data")
	gather_data(algorithm, delay, False)
	plot_iperf(algorithm, delay, False)
	

def gather_data(algorithm, delay, cwnd):
	
	if cwnd == True:
		if (path.exists("{0}_h1_{1}_cwnd_new".format(algorithm, delay))):
			os.remove("{0}_h1_{1}_cwnd_new".format(algorithm, delay))
		if (path.exists("{0}_h2_{1}_cwnd_new".format(algorithm, delay))):
			os.remove("{0}_h2_{1}_cwnd_new".format(algorithm, delay))
		print("Creating the files for IPERF to plot the CWND graph")
		subprocess.Popen("cat cwnd_{0}_h1_{1} | grep sec | head -200 | tr - \" \" | awk '{{if ($12 == \"KBytes\")print $4, int($11*1000)/(1500); else if ($12 == \"MBytes\")print $4, int($11*1000000)/(1500); else print($11)/(1500);}}'> {2}_h1_{3}_cwnd_new".format(algorithm,delay,algorithm,delay), shell=True)
		subprocess.Popen("cat cwnd_{0}_h2_{1} | grep sec | head -200 | tr - \" \" | awk '{{if ($12 == \"KBytes\")print 40+$4, int($11*1000)/(1500); else if ($12 == \"MBytes\")print 40+$4, int($11*1000000)/(1500); else print 40+$4, ($11)/(1500);}}' > {2}_h2_{3}_cwnd_new".format(algorithm,delay,algorithm,delay), shell=True)
		print("Done") 
	else:
		if (path.exists("{0}_h3_{1}_fair_new".format(algorithm, delay))):
			os.remove("{0}_h3_{1}_fair_new".format(algorithm, delay))
		if (path.exists("{0}_h4_{1}_fair_new".format(algorithm, delay))):
			os.remove("{0}_h4_{1}_fair_new".format(algorithm, delay))
		print("Creating the files for IPERF to plot the TCP fairness graph")
		subprocess.Popen("cat fair_{0}_h3_{1} | grep sec | head -100 | tr - \" \" | awk '{{print $4, $8}}' > {2}_h3_{3}_fair_new".format(algorithm,delay,algorithm,delay), shell=True)
		subprocess.Popen("cat fair_{0}_h4_{1} | grep sec | head -100 | tr - \" \" | awk '{{print $4, $8}}' > {2}_h4_{3}_fair_new".format(algorithm,delay,algorithm,delay), shell=True)
		print("Done") 


def plot_iperf(algorithm, delay, cwnd):
	if cwnd == True:		
		if (path.exists("{0}_{1}_cwnd.png".format(algorithm, delay))):
			os.remove("{0}_{1}_cwnd.png".format(algorithm, delay))
		print("Creating the plots for IPERF for the CWND graph")
		plot1 = subprocess.Popen(["gnuplot"], stdin=subprocess.PIPE, encoding='utf8')
		plot1.stdin.write("plot \"{0}_h1_{1}_cwnd_new\" title \"TCP Flow 1\" with linespoints, \"{0}_h2_{1}_cwnd_new\" title \"TCP Flow 2\" with linespoints\n".format(algorithm, delay))
		plot1.stdin.write("set xrange[1:200]\n")
		plot1.stdin.write("set xtics 1,20,200\n")
		plot1.stdin.write("set title \"Change in cwnd (packets) vs Time (1s units) for two TCP flows (rtt = {0} ms) using {1}\"\n".format(delay*2, algorithm.upper()))
		plot1.stdin.write("set xlabel \"Time (seconds)\"\n")
		plot1.stdin.write("set ylabel \"Congestion Window (packets)\"\n")
		plot1.stdin.write("set terminal png\n")
		plot1.stdin.write("set output \"{0}_{1}_cwnd.png\"\n".format(algorithm, delay))
		plot1.stdin.write("replot\n")
		plot1.stdin.write("exit\n")
	else:
		if (path.exists("{0}_{1}_fair.png".format(algorithm, delay))):
			os.remove("{0}_{1}_fair.png".format(algorithm, delay))
		print("Creating the plots for IPERF for the TCP fairness graph")
		plot1 = subprocess.Popen(["gnuplot"], stdin=subprocess.PIPE, encoding='utf8')
		plot1.stdin.write("plot \"{0}_h3_{1}_fair_new\" title \"TCP Flow 1\" with linespoints, \"{0}_h4_{1}_fair_new\" title \"TCP Flow 2\" with linespoints\n".format(algorithm, delay))

		plot1.stdin.write("set xrange[1:100]\n")
		plot1.stdin.write("set xtics 1,10,100\n")
		plot1.stdin.write("set title \"Change in Throughput (Mbps) vs Time (1s units) for two TCP flows (rtt = {0} ms) using {1}\"\n".format(delay*2, algorithm.upper()))
		plot1.stdin.write("set xlabel \"Time (seconds)\"\n")
		plot1.stdin.write("set ylabel \"Throughput (Mbps)\"\n")
		plot1.stdin.write("set terminal png\n")
		plot1.stdin.write("set output \"{0}_{1}_fair.png\"\n".format(algorithm, delay))
		plot1.stdin.write("replot\n")
		plot1.stdin.write("exit\n")

	
if __name__ == '__main__':
	delay = [21, 81, 162]
	algorithm = ['cubic', 'reno' 'westwood', 'vegas']
	
	setLogLevel('info')
	
	#run_tests()
	
	for x in algorithm:
		for y in delay:
			print("CWND for {0} {1}".format(x, y))
			run_tcp_tests_cwnd(x, y)
			print("TCP Fairness for {0} {1}".format(x, y))
			run_tcp_tests_fairness(x, y)
	

