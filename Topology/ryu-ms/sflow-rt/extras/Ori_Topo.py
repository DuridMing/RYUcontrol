#!/usr/bin/env python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.util import customClass
from mininet.link import TCLink

from mininet.util import dumpNodeConnections


# Compile and run sFlow helper script
# - configures sFlow on OVS
# - posts topology to sFlow-RT
# execfile('sflow-rt/extras/sflow.py')
exec(open("./sflow.py").read())

# Rate limit links to 10Mbps
link = customClass({'tc': TCLink}, 'tc,bw=10')

def FTopo():

    net = Mininet(topo=None,link=link ,build=False, ipBase='1.0.0.0/24')

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0' ,controller=RemoteController)

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch)
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch)
    s6 = net.addSwitch('s6', cls=OVSKernelSwitch)
    s7 = net.addSwitch('s7', cls=OVSKernelSwitch)
    s8 = net.addSwitch('s8', cls=OVSKernelSwitch)
    s9 = net.addSwitch('s9', cls=OVSKernelSwitch)
    s10 = net.addSwitch('s10', cls=OVSKernelSwitch)
    s11 = net.addSwitch('s11', cls=OVSKernelSwitch)
    s12 = net.addSwitch('s12', cls=OVSKernelSwitch)
    s13 = net.addSwitch('s13', cls=OVSKernelSwitch)
    s14 = net.addSwitch('s14', cls=OVSKernelSwitch)
    s15 = net.addSwitch('s15', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='1.0.2.1', mac='00:01:00:00:00:37')
    h2 = net.addHost('h2', cls=Host, ip='1.0.2.2',mac='00:01:00:00:00:38')
    h3 = net.addHost('h3', cls=Host, ip='1.0.2.3',mac='00:01:00:00:00:39')
    h4 = net.addHost('h4', cls=Host, ip='1.0.2.4',mac='00:01:00:00:00:3a')
    h5 = net.addHost('h5', cls=Host, ip='1.0.2.5',mac='00:01:00:00:00:3b')
    h6 = net.addHost('h6', cls=Host, ip='1.0.2.6',mac='00:01:00:00:00:3c')
    h7 = net.addHost('h7', cls=Host, ip='1.0.2.7',mac='00:01:00:00:00:3d')
    h8 = net.addHost('h8', cls=Host, ip='1.0.2.8',mac='00:01:00:00:00:3e')
    h9 = net.addHost('h9', cls=Host, ip='1.0.2.9',mac='00:01:00:00:00:3f')
    h10 = net.addHost('h10', cls=Host, ip='1.0.2.10',mac='00:01:00:00:00:40')
    h11 = net.addHost('h11', cls=Host, ip='1.0.2.11',mac='00:01:00:00:00:41')
    h12 = net.addHost('h12', cls=Host, ip='1.0.2.12',mac='00:01:00:00:00:42')
    h13 = net.addHost('h13', cls=Host, ip='1.0.2.13',mac='00:01:00:00:00:43')
    h14 = net.addHost('h14', cls=Host, ip='1.0.2.14',mac='00:01:00:00:00:44')
    h15 = net.addHost('h15', cls=Host, ip='1.0.2.15',mac='00:01:00:00:00:45')
    h16 = net.addHost('h16', cls=Host, ip='1.0.2.16',mac='00:01:00:00:00:46')

    info( '*** Add links\n')
    
    # s1 switch 
    net.addLink(s1, s2)
    net.addLink(s1, s3)
    # s2 switch
    net.addLink(s2,s4)
    net.addLink(s2,s5)
    # s3 switch 
    net.addLink(s3, s6)
    net.addLink(s3, s7)
    # s4 switch
    net.addLink(s4,s8)
    net.addLink(s4,s9)
    net.addLink(s4,s5)
    # s5 switch
    net.addLink(s5,s10)
    net.addLink(s5,s11)
    net.addLink(s5,s6)
    # s6 switch
    net.addLink(s6,s12)
    net.addLink(s6,s13)
    net.addLink(s6,s7)
    # s7 switch
    net.addLink(s7, s14)
    net.addLink(s7, s15)
    # s8 switch
    net.addLink(s8, h2)
    net.addLink(s8, h1)
    # s9 switch
    net.addLink(s9, h3)
    net.addLink(s9, h4)
    # s10 switch
    net.addLink(s10, h5)
    net.addLink(s10, h6)
    # s11 switch
    net.addLink(s11, h7)
    net.addLink(s11, h8)
    # s12 switch
    net.addLink(s12, h9)
    net.addLink(s12, h10)
    # s13 switch
    net.addLink(s13, h11)
    net.addLink(s13, h12)
    # s14 switch
    net.addLink(s14, h13)
    net.addLink(s14, h14)
    # s15 switch
    net.addLink(s15, h15)
    net.addLink(s15, h16)

    info( '*** Starting network\n')
    net.start()
    dumpNodeConnections(net.hosts)

    # info( '*** Starting controllers\n')
    # for controller in net.controllers:
    #     controller.start()

    info( '*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    FTopo()

