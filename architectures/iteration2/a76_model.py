from m5.objects import ArmO3CPU

def configure_a76_o3(cpu):
    # Cortex-A76-ish front end / back end.
    # These are modeling choices, not a perfect BCM2712 description.

    # https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/cortex-a76-laptop-class-performance-with-mobile-efficiency
    # for wide decode, quad issue integer units
    cpu.fetchWidth = 4
    cpu.decodeWidth = 4 
    cpu.renameWidth = 4
    cpu.dispatchWidth = 8
    cpu.issueWidth = 8
    cpu.wbWidth = 8
    cpu.commitWidth = 8

    # https://www.androidauthority.com/cortex-a76-deep-dive-870896/
    # 128 entry instruction window
    cpu.numROBEntries = 128

    # two simd units. no where to put

    # 72 in flight stores and 68 in flight loads
    cpu.LQEntries = 68
    cpu.SQEntries = 72

    # https://developer.arm.com/documentation/100798/0401/Generic-Interrupt-Controller-CPU-interface/About-the-Generic-Interrupt-Controller-CPU-interface
    cpu.createInterruptController() # the A76 has a generic interrupt controller, so the default here is probably okay


def make_cortex_a76_cpu(system):
    num_cpus = 4

    system.cpu = [ArmO3CPU(cpu_id=i) for i in range(num_cpus)]

    for i, cpu in enumerate(system.cpu):
        cpu.clk_domain = system.clk_domain

        configure_a76_o3(cpu)

