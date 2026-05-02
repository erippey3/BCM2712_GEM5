from m5.objects import System, SrcClockDomain, VoltageDomain, AddrRange

def make_a76_system():
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

    return system