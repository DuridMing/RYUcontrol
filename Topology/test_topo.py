# #!/usr/bin/python
# from mininet.cli import CLI
# from mininet.topo import Topo
# from mininet.net import Mininet
# from mininet.node import Controller, RemoteController, OVSController
# from mininet.link import TCLink
# from mininet.util import dumpNodeConnections
# from mininet.log import setLogLevel



# class myTopo(Topo):
#     "Single switch connected to n hosts."

#     def build(self):
#         # switch = self.addSwitch('s1')
#         # for h in range(n):
#         #     # Each host gets 50%/n of system CPU
#         #     host = self.addHost('h%s' % (h + 1),
#         #                     cpu=.5/n)
#         #     # 10 Mbps, 5ms delay, 2% loss, 1000 packet queue
#         #     self.addLink(host, switch, bw=10, delay='5ms', loss=2,
#         #             max_queue_size=1000, use_htb=True)
#         s1 = self.addSwitch('s1')
#         h1 = self.addHost('h1',ip='1.0.2.1')
#         h2 = self.addHost('h2',ip='1.0.2.2')

#         self.addLink(h1 ,s1)
#         self.addLink(h2 ,s1)

# def perfTest():
#     "Create network and run simple performance test"
#     topo = myTopo()
#     net = Mininet(topo=topo, link=TCLink, ipBase='1.0.0.0/24', controller=None)
#     net.addController('c0', controller=RemoteController, port=6633)
    
#     net.start()
#     print("Dumping host connections")
#     dumpNodeConnections(net.hosts)
#     # print("Testing network connectivity")
#     # net.pingAll()
    
#     print("start CLI")
#     CLI(net)

#     net.stop()


# if __name__ == '__main__':
#     setLogLevel('info')
#     perfTest()

#!/usr/bin/python
# File: fourhostnet.py
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import OVSKernelSwitch


def emptyNet():
    "Create an empty network and add nodes to it."

    net = Mininet(ipBase='1.0.0.0/24')

    info('*** Adding controller\n')
    net.addController('c0',controller=RemoteController)

    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='1.0.2.1')
    h2 = net.addHost('h2', ip='1.0.2.2')
    h3 = net.addHost('h3', ip='1.0.2.3')
    h4 = net.addHost('h4', ip='1.0.2.4')

    info('*** Adding switch\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)

    info('*** Creating links\n')
    net.addLink(h1, s2)
    net.addLink(h2, s2)
    net.addLink(h3, s3)
    net.addLink(h4, s3)
    net.addLink(s1 ,s2)
    net.addLink(s1 ,s3)

    info('*** Starting network\n')
    net.start()

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    emptyNet()
