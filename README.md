Leilani Horlander-Cruz
Thomas Leyden
Mininet TCP Congestion Control Simulations using Mininet

# VM Settings
Mininet-2.3.0-210211-ubuntu-18-04-5
Python 2.7.17
Iperf3 3.9
gnuplot 5.2 latchlevel 2

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

# Additional Info
If you are missing certain TCP congestion control algorithms. You may help the following commands helpfull
`/sbin/sysctl net.ipv4.tcp_available_congestion_control`
`sudo /sbin/modprobe tcp_htcp`
Check your max congestion window size if CWND is maxed out at a specific value
`sudo sysctl -a | grep net.core.wmem_max`

