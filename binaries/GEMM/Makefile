# ---------- Config ----------

CXX_NATIVE ?= g++
CXX_X86    ?= x86_64-linux-gnu-g++
CXX_ARM    ?= aarch64-linux-gnu-g++

SRC = gemm.cpp

COMMON_CXXFLAGS = -ggdb3 -std=c++17 -static
COMMON_LDFLAGS  =  -fopenmp

# Native: optimize for whatever CPU this machine has
NATIVE_CXXFLAGS = $(COMMON_CXXFLAGS) -march=native -mtune=native -DON_HARDWARE
NATIVE_LDFLAGS = $(COMMON_LDFLAGS) -lopenblas

# x86-64 cross/native-ish target
# x86-64-v3 is a reasonable modern baseline: AVX2, FMA, BMI2, etc.
# For maximum compatibility, use: -march=x86-64
X86_CXXFLAGS = $(COMMON_CXXFLAGS) -march=x86-64-v3 -mtune=generic
X86_LDFLAGS = $(COMMON_LDFLAGS) -lopenblas_cooperlakep-r0.3.33.dev

# Raspberry Pi 5: Cortex-A76, ARMv8.2-A
# The Cortex-A76 supports NEON/ASIMD as part of AArch64.
ARM_CXXFLAGS = $(COMMON_CXXFLAGS) -mcpu=cortex-a76 -mtune=cortex-a76 -mbranch-protection=none
ARM_LDFLAGS = $(COMMON_LDFLAGS) -lopenblas_cortexa76p-r0.3.33.dev -DON_HARDWARE

# ---------- Targets ----------

.PHONY: all native x86 arm clean

all: native

native: gemm-native

x86: gemm-x86

arm: gemm-arm

gemm-native: $(SRC)
	$(CXX_NATIVE) -o $@ $^ $(NATIVE_CXXFLAGS) $(NATIVE_LDFLAGS)

gemm-x86: $(SRC)
	$(CXX_X86) -o $@ $^ $(X86_CXXFLAGS) $(X86_LDFLAGS)

gemm-arm: $(SRC)
	$(CXX_ARM) -o $@ $^ $(ARM_CXXFLAGS) $(ARM_LDFLAGS)

clean:
	rm -f gemm gemm-native gemm-x86 gemm-arm