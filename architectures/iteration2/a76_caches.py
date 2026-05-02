# general cache to be build upon for Raspberry Pi 5
from m5.objects import Cache, TreePLRURP, WeightedLRURP, StridePrefetcher, SystemXBar
from a76_interconnect import A76L2XBar, A76L3Xbar


class A76L1ICache(Cache):
    size = "64KiB" # directly from TRM
    assoc = 4 # directly from TRM
    tag_latency = 1
    data_latency = 1
    response_latency = 1
    mshrs = 4
    tgts_per_mshr = 20
    replacement_policy = TreePLRURP() # Cortex A76 uses Pseudo-LRU replacement Policy

    def connectCPU(self, cpu):
        self.cpu_side = cpu.icache_port

    def connectBus(self, bus):
        self.mem_side = bus.cpu_side_ports


class A76L1DCache(Cache):
    size = "64KiB" # directly from TRM
    assoc = 4 # directly from TRM
    tag_latency = 1
    data_latency = 1
    response_latency = 1
    mshrs = 8
    tgts_per_mshr = 20
    replacement_policy = TreePLRURP() # Cortex A76 uses Pseudo-LRU replacement Policy

    prefetcher = StridePrefetcher(
        degree = 2,
        distance=1,
        table_entries="64",
        table_assoc=4,

        # A76 load-side prefetcher uses virtual addresses.
        use_virtual_addresses=True,

        # Data-side only.
        on_inst=False,
        on_data=True,
        on_read=True,

        # Start conservative. Later sweep this.
        on_write=False,
        on_miss=True,
    )

    def connectCPU(self, cpu):
        self.cpu_side = cpu.dcache_port

    def connectBus(self, bus):
        self.mem_side = bus.cpu_side_ports


class A76L2Cache(Cache):
    size = "512KiB" # direct from TRM
    assoc = 8 # direct from TRM
    tag_latency = 12
    data_latency = 12
    response_latency = 12
    mshrs = 32
    tgts_per_mshr = 12
    replacement_policy = WeightedLRURP() # A76 uses Dynamic Biased RP which biases replacing clean blocks. This is not an option in GEM5

    prefetcher = StridePrefetcher(
        degree=2,
        distance=1,

        # Store-side A76 prefetcher uses physical addresses.
        use_virtual_addresses=False,

        on_inst=False,
        on_data=True,

        # If you want this to approximate the store-side engine:
        on_read=False,
        on_write=True,

        on_miss=True,
    )

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports


class A76L3Cache(Cache):
    size = '2MiB'
    assoc = 16
    tag_latency = 30
    data_latency = 30
    response_latency = 30
    mshrs = 32
    tgts_per_mshr = 20

    def __init__(self, opts=None):
        super(A76L3Cache, self).__init__()
        if not opts or not opts.l3_size:
            return
        self.size = opts.l3_size

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports 



def attach_a76_cache_hierarchy(system):
    num_cpus = len(system.cpu)

    system.l2bus = [A76L2XBar() for _ in range(num_cpus)]
    system.l2cache = [A76L2Cache() for _ in range(num_cpus)]

    system.l3bus = A76L3Xbar()
    system.l3cache = A76L3Cache()
    system.l3cache.connectCPUSideBus(system.l3bus)

    system.membus = SystemXBar()
    system.l3cache.connectMemSideBus(system.membus)


    for i, cpu in enumerate(system.cpu):
        cpu.icache = A76L1ICache()
        cpu.dcache = A76L1DCache()

        cpu.icache.connectCPU(cpu)
        cpu.dcache.connectCPU(cpu)

        cpu.icache.connectBus(system.l2bus[i])
        cpu.dcache.connectBus(system.l2bus[i])

        system.l2cache[i].connectCPUSideBus(system.l2bus[i])
        system.l2cache[i].connectMemSideBus(system.l3bus)

