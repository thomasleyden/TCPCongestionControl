# TCP Congestion Control
TCP Congestion Control algorithms with mininet

Algorithms:
  * Reno
  * Cubic
  * Westwood
  * Vegas

Make sure to install the following packages before running: 
`sudo apt-get install gnuplot`
`sudo apt-get install iperf3`

Run the following before running any tests to ensure no other processes are running in mininet:
`sudo mn -c`

To run all tests together:
`sudo python dumbbell_topology.py`

/sbin/sysctl net.ipv4.tcp_available_congestion_control
sudo /sbin/modprobe tcp_htcp
