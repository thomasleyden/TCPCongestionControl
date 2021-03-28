#!/usr/bin/env python

"""
Create a network where different switches are connected to
different controllers, by creating a custom Switch() subclass.
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.util import quietRun, dumpNodeConnections
import os
import subprocess
import time
import matplotlib
matplotlib.use('Agg') # force matplotlib to not use any XWindows backend
import matplotlib.pyplot as plt
from os import path

class Dumbbell_Topology(Topo):
	# Dumbbell topology for mininet

	def build(self, delay=2):
		""" 
		For all calculations, we assume a packet size (MTU) of 1500 bytes.
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
		Bandwidth of 984Mbps and a max queue size of 100% * bandwidth * delay.
		"""
		# Bandwidth is in Mbps, delay is in ms, and max queue size is in packets
		# Connect Backbone Router 1 to Backbone Router 2
		self.addLink(s1, s2, cls=TCLink, bw=984, delay='{0}ms'.format(delay), max_queue_size=82*delay, use_htb=True)
		
		"""
		The access routers can transmit/receive at 252Mbps (21p/ms).
		Bandwidth of 252Mbps and a delay of 0ms.
		Max queue size = 20% * bandwidth * delay.
		"""
		# Bandwidth is in Mbps, delay is in ms, and max queue size is in packets
		# Connect Access Router 1 to Backbone Router 1
		self.addLink(s1, s3, cls=TCLink, bw=252, delay='0ms', max_queue_size=21*delay*0.2, use_htb=True)
		# Connect Access Router 2 to Backbone Router 2
		self.addLink(s2, s4, cls=TCLink, bw=252, delay='0ms', max_queue_size=21*delay*0.2, use_htb=True)
		
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
		Bandwidth of 0ms and a max queue size of 100% * bandwidth * delay.
		"""
		# Bandwidth is in Mbps, delay is in ms, and max queue size is in packets
		# Connect Source 1 to Access Router 1
		self.addLink(h1, s3, cls=TCLink, bw=960, delay='0ms', max_queue_size=80*delay, use_htb=True)
		# Connect Source 2 to Access Router 1
		self.addLink(h2, s3, cls=TCLink, bw=960, delay='0ms', max_queue_size=80*delay, use_htb=True)
		# Connect Receiver 1 to Access Router 2
		self.addLink(h3, s4, cls=TCLink, bw=960, delay='0ms', max_queue_size=80*delay, use_htb=True)
		# Connect Receiver 2 to Access Router 2
		self.addLink(h4, s4, cls=TCLink, bw=960, delay='0ms', max_queue_size=80*delay, use_htb=True)


def cleanProbe():
	print("Removing existing TCP probe")
	procs = quietRun('pgrep -f /proc/net/tcpprobe').split()
	for proc in procs:
		output = quietRun('sudo kill -KILL {0}'.format(proc.rstrip()))
		if output != '':
			print(output)
	
def run_tests():
	topo = Dumbbell_Topology(delay=21)
	net = Mininet(topo=topo)
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
	if(path.exists("{0}_tcpprobe_cwnd_{1}.txt".format(algorithm, delay))):
		print("Removing existing file")
		os.remove("{0}_tcpprobe_cwnd_{1}.txt".format(algorithm, delay))
	cleanProbe()
	print("Starting probe")
	output = quietRun('sudo rmmod tcp_probe')
	output = quietRun('sudo modprobe tcp_probe')
	print("Storing the TCP probe results")
	tcpprobe_proc = subprocess.Popen('sudo cat /proc/net/tcpprobe > {0}_tcpprobe_cwnd_{1}.txt'.format(algorithm, delay), shell=True)
	
	topo = Dumbbell_Topology(delay)
	net = Mininet(topo=topo)
	net.start()
	
	h1, h2, h3, h4 = net.getNodeByName('h1', 'h2', 'h3', 'h4')
	host_addr = dict({'h1': h1.IP(), 'h2': h2.IP(), 'h3': h3.IP(), 'h4': h4.IP()})
	print('Host addresses: {0}'.format(host_addr))
	
	if(path.exists("{0}--{1}--{2}--cwnd".format(algorithm, h1, delay))):
		print("Removing existing file")
		os.remove("{0}--{1}--{2}--cwnd".format(algorithm, h1, delay))
	
	if(path.exists("{0}--{1}--{2}--cwnd".format(algorithm, h2, delay))):
		print("Removing existing file")
		os.remove("{0}--{1}--{2}--cwnd".format(algorithm, h2, delay))
	
	# run iperf
	popens = dict()
	popens[h3] = h3.popen(['iperf', '-s', '-p', '5001', '-w', '16m'])
	popens[h4] = h3.popen(['iperf', '-s', '-p', '5001'])
	time.sleep(5)
	
	print('Starting iperf client h1')
	popens[h1] = h1.popen('iperf -c {0} -p 5001 -i 1 -w 16m -Z {1} -t 2000 -y C > iperf_{2}_{3}_{4}'.format(h3.IP(), algorithm, algorithm, h1, delay), shell=True)
	print("250 delay for client 2")
	time.sleep(250)
	print('Starting iperf client h2')
	popens[h2] = h2.popen('iperf -c {0} -p 5001 -i 1 -w 16m -Z {1} -t 1750 -y C > iperf_{2}_{3}_{4}'.format(h4.IP(), algorithm, algorithm, h2, delay), shell=True)

	popens[h1].wait()
	popens[h2].wait()
	
	print("Terminate the iperf servers and tcpprobe processes")
	popens[h3].terminate()
	popens[h4].terminate()
	tcpprobe_proc.terminate()
	
	popens[h3].wait()
	popens[h4].wait()
	tcpprobe_proc.wait()
	
	cleanProbe()
	
	print("Stopping test")
	net.stop()
	
	print("Processing data")
	data_cwnd(algorithm, delay)
	plot_tcpprobe(algorithm, delay)
	

def run_tcp_tests_fairness(algorithm, delay):
	if(path.exists("{0}_tcpprobe_fairness_{1}.txt".format(algorithm, delay))):
		print("Removing existing file")
		os.remove("{0}_tcpprobe_fairness_{1}.txt".format(algorithm, delay))
	cleanProbe()
	print("Starting probe")
	output = quietRun('sudo rmmod tcp_probe')
	output = quietRun('sudo modprobe tcp_probe')
	print("Storing the TCP probe results")
	tcpprobe_proc = subprocess.Popen('sudo cat /proc/net/tcpprobe > {0}_tcpprobe_fairness_{1}.txt'.format(algorithm, delay), shell=True)
	
	topo = Dumbbell_Topology(delay)
	net = Mininet(topo=topo)
	net.start()
	
	h1, h2, h3, h4 = net.getNodeByName('h1', 'h2', 'h3', 'h4')
	host_addr = dict({'h1': h1.IP(), 'h2': h2.IP(), 'h3': h3.IP(), 'h4': h4.IP()})
	print('Host addresses: {0}'.format(host_addr))
	
	if(path.exists("{0}--{1}--{2}--fairness".format(algorithm, h1, delay))):
		print("Removing existing file")
		os.remove("{0}--{1}--{2}--fairness".format(algorithm, h1, delay))
	
	if(path.exists("{0}--{1}--{2}--fairness".format(algorithm, h2, delay))):
		print("Removing existing file")
		os.remove("{0}--{1}--{2}--fairness".format(algorithm, h2, delay))
	
	# run iperf
	popens = dict()
	popens[h3] = h3.popen(['iperf', '-s', '-p', '5001', '-w', '16m'])
	popens[h4] = h3.popen(['iperf', '-s', '-p', '5001'])
	time.sleep(5)
	
	print('Starting iperf client h1')
	popens[h1] = h1.popen('iperf -c {0} -p 5001 -i 1 -w 16m -Z {1} -t 1000 -y C > iperf_{2}_{3}_{4}'.format(h3.IP(), algorithm, algorithm, h1, delay), shell=True)
	print('Starting iperf client h2')
	popens[h2] = h2.popen('iperf -c {0} -p 5001 -i 1 -w 16m -Z {1} -t 1000 -y C > iperf_{2}_{3}_{4}'.format(h4.IP(), algorithm, algorithm, h2, delay), shell=True)

	popens[h1].wait()
	popens[h2].wait()
	
	print("Terminate the iperf servers and tcpprobe processes")
	popens[h3].terminate()
	popens[h4].terminate()
	tcpprobe_proc.terminate()
	
	popens[h3].wait()
	popens[h4].wait()
	tcpprobe_proc.wait()
	
	cleanProbe()
	
	print("Stopping test")
	net.stop()
	
	print("Processing data")
	data_fairness(algorithm, delay)
	plot_iperf(algorithm, delay)
	

def data_cwnd(algorithm, delay):
	
	if (path.exists("{0}_h1_{1}_tcpprobe.txt".format(algorithm, delay))):
		os.remove("{0}_h1_{1}_tcpprobe.txt".format(algorithm, delay))
	if (path.exists("{0}_h2_{1}_tcpprobe.txt".format(algorithm, delay))):
		os.remove("{0}_h2_{1}_tcpprobe.txt".format(algorithm, delay))
	
	f1 = open("{0}_h1_{1}_tcpprobe.txt".format(algorithm, delay), "a")
	f2 = open("{0}_h2_{1}_tcpprobe.txt".format(algorithm, delay), "a")
	f = open("{0}_tcpprobe_cwnd_{1}.txt".format(algorithm, delay), "r")
	print("Reading from file {0}_tcpprobe_cwnd_{1}.txt to plot the CWND graph".format(algorithm, delay))
	
	if f.mode=="r":
		for contents in f:
			contents = contents.split(" ")
			
			if contents[0] != '' and contents[6] != '' and contents[1].startswith('10.0.0.1'):
				data = contents[0]+' '+contents[6]+'\n'
				f1.writelines(data)

			if contents[0] != '' and contents[6] != '' and contents[1].startswith('10.0.0.2'):
				data = contents[0]+' '+contents[6]+'\n'
				f2.writelines(data)
	
	f.close()
	f1.close()
	f2.close()
	
	print("Done")
	

def data_fairness(algorithm, delay):
	
	if (path.exists("{0}_h1_{1}_iperf.txt".format(algorithm, delay))):
		os.remove("{0}_h1_{1}_iperf.txt".format(algorithm, delay))
	if (path.exists("{0}_h2_{1}_iperf.txt".format(algorithm, delay))):
		os.remove("{0}_h2_{1}_iperf.txt".format(algorithm, delay))
	print("Creating the files for IPERF to plot the TCP fairness graph")
	subprocess.Popen("cat {0}-h1-{1} | grep sec | tr - ' ' | awk '{{print $4, $8}}'> {2}_h1_{3}_iperf.txt".format(algorithm,delay,algorithm,delay), shell=True)
	subprocess.Popen("cat {0}-h2-{1} | grep sec | tr - ' ' | awk '{{print $4, $8}}'> {2}_h2_{3}_iperf.txt".format(algorithm,delay,algorithm,delay), shell=True)
	print("Done")


def plot_iperf(algorithm, delay):
	p1=[]
	p2=[]
	p3=[]
	p4=[]
	time.sleep(2)
	f1 = open("{0}_h1_{1}_iperf.txt".format(algorithm, delay), "r")
	f2 = open("{0}_h2_{1}_iperf.txt".format(algorithm, delay), "r")
	for contents in f1:
		contents = contents.split(" ")
		p1.append(float(contents[0].rstrip()))
		p2.append(float(contents[1].rstrip()))
	f1.close()
	for contents in f2:
		contents = contents.split(" ")
		p3.append(float(contents[0].rstrip()))
		p4.append(float(contents[1].rstrip()))
	f2.close()
	
	fig, ax = plt.subplots()
	ax.plot(p1, p2, label="TCP Flow 1")
	ax.plot(p3, p4, label="TCP Flow 2")
	ax.set(xlabel='Time (seconds)', ylabel = 'Throughput (Mbps)', title="TCP Fairness {0} DELAY {1}ms".format(algorithm, delay))
	fig.savefig("{0}_iperf_{1}.png".format(algorithm, delay))
	plt.show()
	

def plot_tcpprobe(algorithm, delay):
	p1=[]
	p2=[]
	p3=[]
	p4=[]
	time.sleep(2)
	f1 = open("{0}_h1_{1}_tcpprobe.txt".format(algorithm, delay), "r")
	f2 = open("{0}_h2_{1}_tcpprobe.txt".format(algorithm, delay), "r")
	for contents in f1:
		contents = contents.split(" ")
		p1.append(float(contents[0].rstrip()))
		p2.append(float(contents[1].rstrip()))
	f1.close()
	for contents in f2:
		contents = contents.split(" ")
		p3.append(float(contents[0].rstrip())+250)
		p4.append(float(contents[1].rstrip()))
	f2.close()
	
	fig, ax = plt.subplots()
	ax.plot(p1, p2, label="TCP Flow 1")
	ax.plot(p3, p4, label="TCP Flow 2")
	ax.set(xlabel='Time (seconds)', ylabel = 'Congestion Window (packets)', title="TCP CWND {0} DELAY {1}ms".format(algorithm, delay))
	fig.savefig("{0}_tcpprobe_{1}.png".format(algorithm, delay))
	plt.show()

	
if __name__ == '__main__':
	delay = [21, 81, 162]
	algorithm = ['reno', 'cubic', 'htcp', 'vegas']
	
	setLogLevel('info')
	
	#run_tests()
	
	for x in algorithm:
		for y in delay:
			print("CWND for {0} {1}".format(x, y))
			run_tcp_tests_cwnd(x, y)
			print("TCP Fairness for {0} {1}".format(x, y))
			run_tcp_tests_fairness(x, y)
	
			
