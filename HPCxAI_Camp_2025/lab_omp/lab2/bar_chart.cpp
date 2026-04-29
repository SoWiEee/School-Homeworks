#include <iostream>
#include <omp.h>
#include <chrono>
#include <cstdlib>
#include <cmath>
#include <vector>
#include "matplotlibcpp.h"
namespace plt = matplotlibcpp;

int main(int argc, char *argv[])
{
    // std::ios::sync_with_stdio(false);
    // std::cin.tie(nullptr);

    if (argc < 2)
    {
        std::cout << "Error: No input file provided." << std::endl;
        return 1;
    }
    char *inputfile_name = argv[1];

    if (argc < 3)
    {
        std::cout << "Error: No output file provided." << std::endl;
        return 1;
    }
    char *outputfile_name = argv[2];

    if (freopen(inputfile_name, "r", stdin) == nullptr)
    {
        std::cout << "Error: Unable to open input file: " << inputfile_name << std::endl;
        return 1;
    }

    std::cout << "Reading input file..." << std::endl;

    int n = 0;

    std::cin >> n;

    // increase cache hit
    std::vector<int> array(n * 5);
    // int **array = (int **)malloc(sizeof(int *) * n);
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < 5; ++j)
            std::cin >> array[i * 5 + j];
    
    // for (int i = 0; i < n; i++)
    // {
    //     array[i] = (int *)malloc(sizeof(int) * 5);
    //     for (int j = 0; j < 5; j++)
    //     {
    //         std::cin >> array[i][j];
    //     }
    // }

    int grade_span[5][5] = {{0}};

    std::cout << "Finish reading input file. Total " << n << " records." << std::endl;
    std::cout << "Start sorting..." << std::endl;
    auto start = std::chrono::steady_clock::now();

    #pragma omp parallel
    {
        int grade_span_local[5][5] = {0};  // 私有區域累積

        #pragma omp for
        for (int j = 0; j < n; j++)
        {
            for (int i = 0; i < 5; i++)
            {
                int score = array[j * 5 + i];
                int bucket = (score >= 90) ? 0 :
                            (score >= 80) ? 1 :
                            (score >= 70) ? 2 :
                            (score >= 60) ? 3 :
                            (score >= 0)  ? 4 : -1;

                if (bucket != -1)
                    grade_span_local[i][bucket]++;
                else
                    printf("error");
            }
        }

        // join results
        #pragma omp critical
        {
            for (int i = 0; i < 5; i++)
                for (int k = 0; k < 5; k++)
                    grade_span[i][k] += grade_span_local[i][k];
        }
    }

    auto end = std::chrono::steady_clock::now();
    std::cout << "Sorting complete." << std::endl;
    std::cout << "Sorting Time: " << std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count() << "ms" << std::endl;

    std::cout << "Start plotting..." << std::endl;

    for(int i=0;i<5;i++){
        std::vector<double> x = {0+0.8*i, 5+0.8*i, 10+0.8*i, 15+0.8*i, 20+0.8*i};
        std::vector<double> h = {(double)grade_span[i][0], (double)grade_span[i][1], (double)grade_span[i][2], (double)grade_span[i][3], (double)grade_span[i][4]};
        plt::bar(x, h);   
    }
    std::vector<double> x_positions = {1.6, 6.6, 11.6, 16.6, 21.6};
    std::vector<std::string> x_labels = {"100-90", "90-80", "80-70", "70-60", "below 60"};
    plt::xticks(x_positions, x_labels);
    plt::save(outputfile_name);
    std::cout << "Plotting complete." << std::endl;
    std::cout << "Saved as " << outputfile_name << std::endl;

    return 0;
}