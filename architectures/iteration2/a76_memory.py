from m5.objects import MemCtrl, DDR4_2400_4x16




def attach_rpi5_memory(system):    
    # Create a DDR4 memory controller and connect it to the membus
    system.mem_ctrl = MemCtrl()
    # the Raspberry Pi uses LPDDR4X-4267 which is not available in GEM5
    # 
    system.mem_ctrl.dram = DDR4_2400_4x16()
    system.mem_ctrl.dram.range = system.mem_ranges[0]
    system.mem_ctrl.port = system.membus.mem_side_ports

    # Connect the system to the membus
    system.system_port = system.membus.cpu_side_ports