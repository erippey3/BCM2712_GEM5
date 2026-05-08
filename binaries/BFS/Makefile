# ---------- Config ----------

CXX_NATIVE ?= g++
CXX_X86    ?= x86_64-linux-gnu-g++
CXX_ARM    ?= aarch64-linux-gnu-g++

SRC = bfs.cpp

COMMON_CXXFLAGS = -ggdb3 -std=c++17 -static
COMMON_LDFLAGS  =  -fopenmp

# Native: optimize for whatever CPU this machine has
NATIVE_CXXFLAGS = $(COMMON_CXXFLAGS) -march=native -mtune=native -DON_HARDWARE
NATIVE_LDFLAGS = $(COMMON_LDFLAGS) -lgraphblas

# x86-64 cross/native-ish target
# x86-64-v3 is a reasonable modern baseline: AVX2, FMA, BMI2, etc.
# For maximum compatibility, use: -march=x86-64
X86_CXXFLAGS = $(COMMON_CXXFLAGS) -march=x86-64-v3 -mtune=generic
X86_LDFLAGS = $(COMMON_LDFLAGS) -lgraphblas.x86

# Raspberry Pi 5: Cortex-A76, ARMv8.2-A
# The Cortex-A76 supports NEON/ASIMD as part of AArch64.
ARM_CXXFLAGS = $(COMMON_CXXFLAGS) -mcpu=cortex-a76 -mtune=cortex-a76 -mbranch-protection=none
ARM_LDFLAGS = $(COMMON_LDFLAGS) -lgraphblas.arm -DON_HARDWARE

# ---------- Targets ----------

.PHONY: all native x86 arm clean

all: arm

native: bfs-native

x86: bfs-x86

arm: bfs-arm

bfs-native: $(SRC)
	$(CXX_NATIVE) -o $@ $^ $(NATIVE_CXXFLAGS) $(NATIVE_LDFLAGS)

bfs-x86: $(SRC)
	$(CXX_X86) -o $@ $^ $(X86_CXXFLAGS) $(X86_LDFLAGS)

bfs-arm: $(SRC)
	$(CXX_ARM) -o $@ $^ $(ARM_CXXFLAGS) $(ARM_LDFLAGS)

clean:
	rm -f bfs bfs-native bfs-x86 bfs-arm