import argparse
from m5.objects import Process, SEWorkload, Root
import m5
from m5.util import addToPath
from a76_caches import attach_a76_cache_hierarchy
from a76_model import make_cortex_a76_cpu
from a76_memory import attach_rpi5_memory
from a76_system import make_a76_system

addToPath("/opt/gem5/configs")
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

system = make_a76_system()

make_cortex_a76_cpu(system)

attach_a76_cache_hierarchy(system)

attach_rpi5_memory(system)

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