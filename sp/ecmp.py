from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import dpid as dpid_lib
from ryu.lib import stplib
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.ofproto import ofproto_v1_3_parser
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp

import random

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    def add_local(self, datapath, local, port):
	#self.logger.info("add local %s %s", local, port)
        parser = datapath.ofproto_parser
        
	# add ip
	match = parser.OFPMatch(eth_type=0x0800, ipv4_dst=local)
        actions = [parser.OFPActionOutput(port)]
        self.add_flow(datapath, 1, match, actions)

	# add arp
        match = parser.OFPMatch(eth_type=0x0806,arp_tpa=local)
        actions = [parser.OFPActionOutput(port)]
        self.add_flow(datapath, 1, match, actions)
    
    def pkt_out(self, msg, actions):
        datapath = msg.datapath
	in_port = msg.match['in_port']
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

	data = None
	if msg.buffer_id == ofproto.OFP_NO_BUFFER:
	    data = msg.data
	out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
	                          in_port=in_port, actions=actions, data=data)
	datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        dpid = datapath.id

        pkt = packet.Packet(msg.data)
        _eth = pkt.get_protocols(ethernet.ethernet)[0]
        _arp = pkt.get_protocol(arp.arp)
        _ipv4 = pkt.get_protocol(ipv4.ipv4)
	_tcp = pkt.get_protocol(tcp.tcp)

	# if parse fail, the object will be None
	#self.logger.info("packet in %s", _tcp)

	# here define ip_dst
	if _arp:
	    ip_dst = _arp.dst_ip
	elif _ipv4:
	    ip_dst = _ipv4.dst
	else: return
	
	#self.logger.info("packet in %d %s %s", dpid, ip_dst, in_port)
        #self.logger.info("%d %d", int("10.0.0.2"), int("10.0.0.1"))
	
	mod = (dpid-1)%4

	# edge switch
	# need to know the hosts it connect
	if (dpid<=16) and ((mod==0) or (mod==1)): 
	    pod = (dpid-1)/4
	    local1 = "10.0.0.%d" % (pod*4+1+mod*2)
	    local2 = "10.0.0.%d" % (pod*4+1+mod*2+1)
	    if (ip_dst==local1):
                self.add_local(datapath, local1, 1)
                actions = [parser.OFPActionOutput(1)]	        
		self.pkt_out(msg, actions)
		return
	    if (ip_dst==local2):
	        self.add_local(datapath, local2, 2)
                actions = [parser.OFPActionOutput(2)]
	        self.pkt_out(msg, actions)
		return
	        
	# aggre switch
	# need to know its subnet
	# count the boundary
        if (dpid<=16) and ((mod==2) or (mod==3)): 
			pod = (dpid-1)/4
			num = int(ip_dst.split(".")[3])
			b0 = (pod*4+1)
			b1 = (pod*4+1+1)
			b2 = (pod*4+1+3)
	    if (num>=b0) and (num<=b1):
	        #self.logger.info("here1")
                self.add_local(datapath, ip_dst, 1)
                actions = [parser.OFPActionOutput(1)]	        
		self.pkt_out(msg, actions)
		return
	    elif (num>b1) and (num<=b2):
	        #self.logger.info("here2")
	        self.add_local(datapath, ip_dst, 2)
                actions = [parser.OFPActionOutput(2)]
	        self.pkt_out(msg, actions)
		return
	
	# core switch
	# 4 ifs for 4 pods
        if (dpid>16): 
	    num = int(ip_dst.split(".")[3])
	    if (num<=4):
	        down_port = 1
	    elif (num<=8):
	        down_port = 2
	    elif (num<=12):
	        down_port = 3
	    elif (num<=16):
	        down_port = 4
            
	    self.add_local(datapath, ip_dst, down_port)
            actions = [parser.OFPActionOutput(down_port)]	        
	    self.pkt_out(msg, actions)
	    return

	# an upstream need to be hashed
	# first, define the hash string
	# we already have ip_dst, still need ip_src, src_port, dst_port
	if _arp:
	    ip_src = _arp.src_ip
	elif _ipv4:
	    ip_src = _ipv4.src
	else:
	    ip_src = "unknown"

	if _tcp:
	    src_port = "%d" % _tcp.src_port
	    dst_port = "%d" % _tcp.dst_port
	else:
	    src_port = "%d" % random.randint(1, 10086)
	    dst_port = "noTCP"
	magic = "%d" % random.randint(1, 99221)

	out_port = (abs(hash(ip_dst+ip_src+src_port+dst_port+magic))%2) + 3
        actions = [parser.OFPActionOutput(out_port)]
	self.logger.info("dpid: %d, <%s, %s, %s, %s, %s> up to %s", dpid, ip_src, ip_dst, src_port, dst_port, magic, out_port)
        
	# add flow to a TCP flow
	if dst_port!="noTCP":
	    match = parser.OFPMatch(eth_type=0x0800, ipv4_dst=ip_dst, ipv4_src=ip_src, ip_proto=0x06, tcp_src=int(src_port), tcp_dst=int(dst_port))
            self.add_flow(datapath, 2, match, actions)
        
	# send pkt-out
	self.pkt_out(msg, actions)
	
