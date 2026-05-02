# general cache to be build upon for Raspberry Pi 5

import m5
from m5.objects import Cache


class L1ICache(Cache):
    size = "64KiB"
    assoc = 4
    tag_latency = 4
    data_latency = 4
    response_latency = 4
    mshrs = 4
    tgts_per_mshr = 20

    def connectCPU(self, cpu):
        self.cpu_side = cpu.icache_port

    def connectBus(self, bus):
        self.mem_side = bus.cpu_side_ports


class L1DCache(Cache):
    size = "64KiB"
    assoc = 4
    tag_latency = 4
    data_latency = 4
    response_latency = 4
    mshrs = 8
    tgts_per_mshr = 20

    def connectCPU(self, cpu):
        self.cpu_side = cpu.dcache_port

    def connectBus(self, bus):
        self.mem_side = bus.cpu_side_ports


class L2Cache(Cache):
    size = "512KiB"
    assoc = 8
    tag_latency = 12
    data_latency = 12
    response_latency = 12
    mshrs = 20
    tgts_per_mshr = 12

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports


class L3Cache(Cache):
    size = '2MiB'
    assoc = 16
    tag_latency = 30
    data_latency = 30
    response_latency = 30
    mshrs = 32
    tgts_per_mshr = 20

    def __init__(self, opts=None):
        super(L3Cache, self).__init__()
        if not opts or not opts.l3_size:
            return
        self.size = opts.l3_size

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports 
