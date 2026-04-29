NVCXX = nvc++
NVCXXFLAGS = -O0 -std=c++11 -fast -acc -gpu=cc70 -Minfo=accel
MNIST=-I/work/HPC_SCAMP/gpu_task/mnist/include
TARGETS = nn

.PHONY: all
all: $(TARGETS)

%: %.cpp
	$(NVCXX) $(NVCXXFLAGS) $(MNIST) -o $@ $<

clean:
	rm -f $(TARGETS)
