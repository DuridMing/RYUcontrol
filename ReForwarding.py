# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
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


from operator import attrgetter
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
import Switch13

class ReForwarding(Switch13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(ReForwarding, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        # datapath.send_msg(req)

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         '
                         'in-port  eth-dst           '
                         'out-port packets  bytes')
        self.logger.info('---------------- '
                         '-------- ----------------- '
                         '-------- -------- --------')
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
            if stat.instructions[0].actions:
                self.logger.info('%016x %8x %17s %8x %8d %8d',
                                 ev.msg.datapath.id,
                                 stat.match['in_port'], stat.match['eth_dst'],
                                 stat.instructions[0].actions[0].port,
                                 stat.packet_count, stat.byte_count)
            else:
                self.logger.info('%016x %8x %17s %8x %8d %8d',
                                 ev.msg.datapath.id,
                                 stat.match['in_port'], stat.match['eth_dst'],
                                 -1,
                                 stat.packet_count, stat.byte_count)
                # print('%016x %8x %17s %8x %8d %8d'%(
                #                  ev.msg.datapath.id,
                #                  stat.match['in_port'], stat.match['eth_dst'],
                #                  -1,
                #                  stat.packet_count, stat.byte_count))

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        pk_stat = []

        self.logger.info('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _Over_and_reforward(self, ev):
        body = ev.msg.body

        for stat in sorted([flow for flow in body if flow.priority == 1],
                            key=lambda flow: (flow.match['in_port'],
                            flow.match['eth_dst'])):
            if stat.match['in_port'] == 1:
                if stat.packet_count > 10 and stat.packet_count <20:
                    self.ReForward(datapath=ev.msg.datapath ,match=stat.match)
                if stat.packet_count > 10:
                    self.logger.info('\033[31mWARN:too more packets\033[0m')
                        

    def ReForward(self, datapath , match):
        # in_port=1,src=10.0.0.1,dst=10.0.0.2,udp,udp_dst=5555--->group id 50
        self.logger.info('\033[31mWARN: Start Reforwarding ! \033[0m')
        
        eth_src = match['eth_src']
        eth_dst = match['eth_dst']
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(in_port=1, eth_dst=eth_dst ,eth_src=eth_src)
        # match = parser.OFPMatch(in_port=1, ipv4_src="10.0.0.1" ,ipv4_dst="10.0.0.3")

        # set rule using group table
        # set priority
        actions = [parser.OFPActionGroup(50)]

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            match=match,
            cookie=0,
            command=ofproto.OFPFC_ADD,
            priority=3,
            instructions=inst,
        )

        datapath.send_msg(mod)
    
    def Reset_count(self ,datapath ,in_port ,table_id):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        # action = [ofp_parser.OFPActionOutput(ofp.OFPFF_RESET_COUNTS, [])]
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_CLEAR_ACTIONS, [])]


        match = ofp_parser.OFPMatch(in_port=in_port )
        mod = ofp_parser.OFPFlowMod(datapath=datapath,
                                table_id=table_id,
                                match=match,
                                priority=1,
                                flags=ofp.OFPFF_RESET_COUNTS, # this flag setting the switch counting to reset
                                instructions=[])

        datapath.send_msg(mod)
