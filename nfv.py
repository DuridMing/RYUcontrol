#!/usr/bin/env python
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.link import Link,TCLink,Intf
from mininet.node import Controller,RemoteController
 
if '__main__' == __name__:
  net = Mininet(link=TCLink)
  h1 = net.addHost('h1', ip="10.0.0.1/24", mac="00:00:00:00:00:01")
  h2 = net.addHost('h2', ip="10.0.0.2/24", mac="00:00:00:00:00:02")
  h3 = net.addHost('h3', ip="10.0.0.3/24", mac="00:00:00:00:00:03")
  s1 = net.addSwitch('s1')
  c0 = net.addController('c0', controller=RemoteController)
  net.addLink(h1, s1)
  net.addLink(h2, s1)
  net.addLink(h3, s1)
  net.build()
  c0.start()
  s1.start([c0])

  # rules for s1
  h1.cmd("arp -s 10.0.0.2 00:00:00:00:00:02")
  h1.cmd("arp -s 10.0.0.3 00:00:00:00:00:03")
  h2.cmd("arp -s 10.0.0.1 00:00:00:00:00:01")
  h2.cmd("arp -s 10.0.0.3 00:00:00:00:00:03")
  h3.cmd("arp -s 10.0.0.1 00:00:00:00:00:01")
  h3.cmd("arp -s 10.0.0.2 00:00:00:00:00:02") 
  h2.cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")
  h2.cmd("iptables -A FORWARD -p tcp --destination-port 8080 -j ACCEPT")
  h2.cmd("iptables -A FORWARD -p tcp --destination-port 80 -j DROP")
  s1.cmd("ovs-ofctl add-flow s1 priority=1,in_port=1,actions=output:3")
  s1.cmd("ovs-ofctl add-flow s1 priority=1,in_port=3,actions=output:1")
  s1.cmd("ovs-ofctl add-flow s1 priority=10,ip,in_port=1,actions=mod_dl_dst=00:00:00:00:00:02,output:2")
  s1.cmd("ovs-ofctl add-flow s1 priority=10,ip,in_port=3,actions=mod_dl_dst=00:00:00:00:00:02,output:2")
  s1.cmd("ovs-ofctl add-flow s1 priority=10,ip,in_port=2,nw_dst=10.0.0.3,actions=mod_dl_dst=00:00:00:00:00:03,output:3")
  s1.cmd("ovs-ofctl add-flow s1 priority=10,ip,in_port=2,nw_dst=10.0.0.1,actions=mod_dl_dst=00:00:00:00:00:01,output:1")


  CLI(net)
  net.stop()
