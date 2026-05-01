

def configure_a76_o3(cpu):
    # Cortex-A76-ish front end / back end.
    # These are modeling choices, not a perfect BCM2712 description.

    cpu.fetchWidth = 4
    cpu.decodeWidth = 4
    cpu.renameWidth = 4
    cpu.dispatchWidth = 4
    cpu.issueWidth = 8
    cpu.wbWidth = 8
    cpu.commitWidth = 4

    cpu.numROBEntries = 128

    #cpu.numIQEntries = 64

    # Roughly A76-shaped load/store pressure.
    cpu.LQEntries = 68
    cpu.SQEntries = 72