CXX = g++
CXXFLAGS = -O3

.PHONY: all
all: bar_chart

bar_chart: bar_chart.cpp
	$(CXX) $(CXXFLAGS) -fopenmp -o bar_chart bar_chart.cpp \
    -I/project/ACD114003/2025summer/omp-mpi/venv/lib/python3.6/site-packages/numpy/core/include \
	-I/usr/include/python3.6m \
    -L/project/ACD114003/2025summer/omp-mpi/venv/lib \
    -lpython3.6m

.PHONY: clean
clean:
	rm -f bar_chart
