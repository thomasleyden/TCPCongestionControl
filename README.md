# TCP Congestion Control
TCP Congestion Control algorithms with mininet

Algorithms:
  * Reno
  * Cubic
  * HTCP
  * Vegas

Make sure to install the iperf3 package before running: 
`sudo apt-get install iperf3`

Run the following before running any tests to ensure no other processes are running in mininet:
`sudo mn -c`

To run all tests together:
`sudo python dumbbell_topology.py`
