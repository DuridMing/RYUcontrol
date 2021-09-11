from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import OVSKernelSwitch


def testNet():
    "Create an empty network and add nodes to it."

    net = Mininet(ipBase='1.0.0.0/24')

    info('*** Adding controller\n')
    net.addController('c0',controller=RemoteController)

    info('*** Adding hosts\n')
    h1 = net.addHost('h1' ,mac='00:00:00:00:00:01')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02')
    info('*** Adding switch\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch)
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch)

    info('*** Creating links\n')

    info('*** Creating host links\n')
    net.addLink(s4,h1)
    net.addLink(s5,h2)

    info('*** Creating switch links\n')
    net.addLink(s1,s4)
    net.addLink(s1,s5)
    net.addLink(s2,s4)
    net.addLink(s2,s5)
    net.addLink(s3,s4)
    net.addLink(s3,s5)

    info('*** Starting network\n')
    net.start()

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    testNet()
