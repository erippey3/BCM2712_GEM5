# import the m5 (gem5) library created when gem5 is built
import argparse
import m5
import sys
from m5.objects import *
from caches import *
from A76 import configure_a76_o3

# Add the common scritps to our path
m5.util.addToPath("/opt/gem5/configs")
# import the SimpleOpts module
from common import SimpleOpts


default_binary = 'ls'


# positional binary
SimpleOpts.add_option("binary", nargs="?", default=default_binary,
                      help="Binary to run")

SimpleOpts.add_option(
    "binary_args",
    nargs=argparse.REMAINDER,
    default=[],
    help="Arguments passed to the binary"
)


args = SimpleOpts.parse_args()

binary = args.binary
binary_args = args.binary_args

# create the system we are going to simulate 
system = System()

# Set the clock frequency of the system and its children
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '2400MHz' # RPI default clock
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the system 
system.mem_mode = 'timing'                  # Use timing accesses
system.mem_ranges = [AddrRange('8GiB')]    # Same as Pi Tested 

system.cache_line_size = 64 # general default


num_cpus = 4 # the number of CPUs in the BCM2712

system.cpu = [ArmO3CPU(cpu_id=i) for i in range(num_cpus)]

# create per CPU L2
system.l2bus = [L2XBar() for _ in range(num_cpus)]
system.l2cache = [L2Cache() for _ in range(num_cpus)]

# shared L3 Cache
system.l3bus = L3XBar()
system.l3cache = L3Cache()
system.l3cache.connectCPUSideBus(system.l3bus)

# Create Memory Bus and connect to L3
system.membus = SystemXBar()
system.l3cache.connectMemSideBus(system.membus)



for i, cpu in enumerate(system.cpu):
    cpu.clk_domain = system.clk_domain
    
    configure_a76_o3(cpu)

    cpu.icache = L1ICache()
    cpu.dcache = L1DCache()

    # Connect the instruction and data caches to the CPU
    cpu.icache.connectCPU(cpu)
    cpu.dcache.connectCPU(cpu)

    # Hook the CPU ports up to the local L2
    cpu.icache.connectBus(system.l2bus[i])
    cpu.dcache.connectBus(system.l2bus[i])

    system.l2cache[i].connectCPUSideBus(system.l2bus[i])
    system.l2cache[i].connectMemSideBus(system.l3bus)

    cpu.createInterruptController()

    


# Create a DDR4 memory controller and connect it to the membus
system.mem_ctrl = MemCtrl()
# the Raspberry Pi uses LPDDR4X-4267 which is not available in GEM5
# 
system.mem_ctrl.dram = DDR4_2400_4x16()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Connect the system to the membus
system.system_port = system.membus.cpu_side_ports







# create a process for application
process = Process()
process.executable = binary
# cmd is a list which begins with the executable
process.cmd = [binary] + binary_args
system.workload = SEWorkload.init_compatible(binary)

# set the cpu to use the process as its workload and create thread contexts
for cpu in system.cpu:
    cpu.workload = process
    cpu.createThreads()

# set up the root SimObjects and start the simulation
root = Root(full_system = False, system = system)
# instantiate all of the objects we've created above 
m5.instantiate()

exit_event = m5.simulate()