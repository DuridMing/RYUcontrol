# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.

#

# Licensed under the Apache License, Version 2.0 (the "License");

# you may not use this file except in compliance with the License.

# You may obtain a copy of the License at

#

#    http://www.apache.org/licenses/LICENSE-2.0

#

# Unless required by applicable law or agreed to in writing, software

# distributed under the License is distributed on an "AS IS" BASIS,

# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or

# implied.

# See the License for the specific language governing permissions and

# limitations under the License.

 

from ryu.base import app_manager

from ryu.controller import mac_to_port

from ryu.controller import ofp_event

from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER

from ryu.controller.handler import set_ev_cls

from ryu.ofproto import ofproto_v1_3

from ryu.lib.mac import haddr_to_bin

from ryu.lib.packet import packet

from ryu.lib.packet import ethernet

from ryu.lib.packet import ether_types

from ryu.lib import mac

from ryu.topology import event, switches

from ryu.topology.api import get_switch, get_link

from ryu.app.wsgi import ControllerBase

from collections import defaultdict

 

#switches

myswitches = []

 

#mymac[srcmac]->(switch, port)

mymac={}

 

#adjacency map [sw1][sw2]->port from sw1 to sw2

adjacency=defaultdict(lambda:defaultdict(lambda:None))

 

datapath_list={}

 

def minimum_distance(distance, Q):

  #print( "minimum_distance() is called", " distance=", distance, " Q=", Q

  min = float('Inf')

  node = 0

  for v in Q:

    if distance[v] < min:

      min = distance[v]

      node = v

  return node

 

def get_path (src,dst,first_port,final_port):

  #Dijkstra's algorithm

  global myswitches, adjacency

  print( "get_path is called, src=",src," dst=",dst, " first_port=", first_port, " final_port=", final_port)

  distance = {}

  previous = {}

 

  for dpid in myswitches:

    distance[dpid] = 9999

    previous[dpid] = None

 

  distance[src]=0

  Q=set(myswitches)

  #print( "Q=", Q

 

  while len(Q)>0:

    u = minimum_distance(distance, Q)

    #print( "u=", u

    Q.remove(u)

    #print( "After removing ", u, " Q=", Q

    for p in myswitches:

     if adjacency[u][p]!=None:

        #print( u, "--------",  p

        w = 1

        if distance[u] + w < distance[p]:

          distance[p] = distance[u] + w

          previous[p] = u

 

  #print( "distance=", distance, " previous=", previous

  r=[]

  p=dst

  r.append(p)

  q=previous[p]

 

  while q is not None:

    if q == src:

      r.append(q)

      break

    p=q

    r.append(p)

    q=previous[p]

 

  r.reverse()

  if src==dst:

    path=[src]

  else:

    path=r

 

  # Now add the ports

  r = []

  in_port = first_port

  for s1,s2 in zip(path[:-1],path[1:]):

    out_port = adjacency[s1][s2]

    r.append((s1,in_port,out_port))

    in_port = adjacency[s2][s1]

  r.append((dst,in_port,final_port))

  return r

 

class ProjectController(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

 

    def __init__(self, *args, **kwargs):

        super(ProjectController, self).__init__(*args, **kwargs)

        self.mac_to_port = {}

        self.topology_api_app = self

 

    # Handy function that lists all attributes in the given object

    def ls(self,obj):

        print(("\n".join([x for x in dir(obj) if x[0] != "_"])))

 

    def add_flow(self, datapath, in_port, dst, actions):

        ofproto = datapath.ofproto

        parser = datapath.ofproto_parser     

        match = datapath.ofproto_parser.OFPMatch(

            in_port=in_port, eth_dst=dst)

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = datapath.ofproto_parser.OFPFlowMod(

            datapath=datapath, match=match, cookie=0,

            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,

            priority=ofproto.OFP_DEFAULT_PRIORITY, instructions=inst)

        datapath.send_msg(mod)

 

    def install_path(self, p, ev, src_mac, dst_mac):

       print( "install_path is called")

       #print( "p=", p, " src_mac=", src_mac, " dst_mac=", dst_mac

       msg = ev.msg

       datapath = msg.datapath

       ofproto = datapath.ofproto

       parser = datapath.ofproto_parser

 

       for sw, in_port, out_port in p:

         print( src_mac,"->", dst_mac, "via ", sw, " in_port=", in_port, " out_port=", out_port)

         match=parser.OFPMatch(in_port=in_port, eth_src=src_mac, eth_dst=dst_mac)

         actions=[parser.OFPActionOutput(out_port)]

         datapath=datapath_list[sw]

         inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS , actions)]

         mod = datapath.ofproto_parser.OFPFlowMod(

            datapath=datapath, match=match, idle_timeout=0, hard_timeout=0,

            priority=1, instructions=inst)

         datapath.send_msg(mod)

 

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)

    def switch_features_handler(self , ev):

         print( "switch_features_handler is called")

         datapath = ev.msg.datapath

         ofproto = datapath.ofproto

         parser = datapath.ofproto_parser

         match = parser.OFPMatch()

         actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]

         inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS , actions)]

         mod = datapath.ofproto_parser.OFPFlowMod(

         datapath=datapath, match=match, cookie=0,

            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,

            priority=0, instructions=inst)

         datapath.send_msg(mod)

 

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)

    def _packet_in_handler(self, ev):

        #print( "packet_in event:", ev.msg.datapath.id, " in_port:", ev.msg.match['in_port']

        msg = ev.msg

        datapath = msg.datapath

        ofproto = datapath.ofproto

        parser = datapath.ofproto_parser

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)

        eth = pkt.get_protocol(ethernet.ethernet)

        #print( "eth.ethertype=", eth.ethertype

 

        #avodi broadcast from LLDP

        if eth.ethertype==35020:

          return

        dst = eth.dst

        src = eth.src

        dpid = datapath.id

        #print( "src=", src, " dst=", dst, " type=", hex(eth.ethertype)

        #print( "adjacency=", adjacency

        self.mac_to_port.setdefault(dpid, {})

 

        if src not in mymac.keys():

           mymac[src]=( dpid,  in_port)

            #print( "mymac=", mymac

 

        if dst in mymac.keys():

            p = get_path(mymac[src][0], mymac[dst][0], mymac[src][1], mymac[dst][1])

            print( "Path=", p)

            self.install_path(p, ev, src, dst)

            out_port = p[0][2]

        else:

            out_port = ofproto.OFPP_FLOOD

 

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time

        if out_port != ofproto.OFPP_FLOOD:

            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)

 

        data=None

        if msg.buffer_id==ofproto.OFP_NO_BUFFER:

           data=msg.data

 

        if out_port == ofproto.OFPP_FLOOD:

           #print( "FLOOD"

           while len(actions) > 0 : actions.pop()

           for i in range(1,23):

              actions.append(parser.OFPActionOutput(i))

           #print( "actions=", actions

           out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,

                                  in_port=in_port, actions=actions, data=data)

           datapath.send_msg(out)  

        else:     

          #print( "unicast"

          out = parser.OFPPacketOut(

              datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,

              actions=actions, data=data)

          datapath.send_msg(out)

   

    events = [event.EventSwitchEnter,

             event.EventSwitchLeave, event.EventPortAdd,

              event.EventPortDelete, event.EventPortModify,

              event.EventLinkAdd, event.EventLinkDelete]

    @set_ev_cls(events)

    def get_topology_data(self, ev):

        print( "get_topology_data() is called")

        global myswitches, adjacency, datapath_list

        switch_list = get_switch(self.topology_api_app, None)

        myswitches=[switch.dp.id for switch in switch_list]

        for switch in switch_list:

          datapath_list[switch.dp.id]=switch.dp

        print( "datapath_list=", datapath_list)

        print( "myswitches=", myswitches)

        links_list = get_link(self.topology_api_app, None)

        print( "links_list=", links_list)

        mylinks=[(link.src.dpid,link.dst.dpid,link.src.port_no,link.dst.port_no) for link in links_list]

        for s1,s2,port1,port2 in mylinks:

          print( "type(s1)=", type(s1), " type(port1)=", type(port1))

          adjacency[s1][s2]=port1

          adjacency[s2][s1]=port2

          print( s1,":", port1, "<--->",s2,":",port2)
