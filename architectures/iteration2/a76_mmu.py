from m5.objects import ArmMMU

class A76MMU(ArmMMU):

    # L2 TLB
    # https://developer.arm.com/documentation/100798/0401/Memory-Management-Unit/TLB-organization/L2-TLB
    l2_shared = ArmMMU.l2_shared
    l2_shared.size = 1280
    l2_shared.assoc = 5 # five way set associative

    # L1 Instruction TLB
    # https://developer.arm.com/documentation/100798/0401/Memory-Management-Unit/TLB-organization/Instruction-L1-TLB
    itb = ArmMMU.itb
    itb.size = 48
    itb.assoc = 48 # fully associative

    # L1 Data TLB
    # https://developer.arm.com/documentation/100798/0401/Memory-Management-Unit/TLB-organization/Data-L1-TLB
    dtb = ArmMMU.dtb
    dtb.size = 48
    dtb.assoc = 48 # fully associative