# Compiler and flags for the CPU version
CPPCXX = g++
CPPCXXFLAGS = -O0 -std=c++11

# Compiler and flags for the GPU version
NVCXX = nvc++
NVCXXFLAGS = -O0 -std=c++11 -fast -acc -gpu=cc70 -Minfo=accel

# Target executables
CPU_TARGET = matrix_mul_cpu
GPU_TARGET = matrix_mul_gpu

.PHONY: all clean

all: $(CPU_TARGET) $(GPU_TARGET)

# Rule for CPU version
$(CPU_TARGET): matrix_mul_cpu.cc
	$(CPPCXX) $(CPPCXXFLAGS) -o $@ $<

# Rule for GPU version
$(GPU_TARGET): matrix_mul_gpu.cu
	$(NVCXX) $(NVCXXFLAGS) -o $@ $<

clean:
	rm -f $(CPU_TARGET) $(GPU_TARGET)