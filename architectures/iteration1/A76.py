

def configure_a76_o3(cpu):

    cpu.fetchWidth = 4
    cpu.decodeWidth = 4
    cpu.renameWidth = 4
    cpu.dispatchWidth = 4
    cpu.issueWidth = 8
    cpu.wbWidth = 8
    cpu.commitWidth = 4

    cpu.numROBEntries = 128

    cpu.LQEntries = 68
    cpu.SQEntries = 72