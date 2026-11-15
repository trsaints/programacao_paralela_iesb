#include <cstdio>
#include <vector>
#include <chrono>
#include <cstdlib>
#include <omp.h>

int main(int argc, char **argv)
{
    int N = (argc > 1) ? std::atoi(argv[1]) : 2000;
    int P = (argc > 2) ? std::atoi(argv[2]) : 30;

    std::vector<float> a(N * N);
    std::vector<float> b(N * N);

    for (int i = 0; i < N * N; i++)
    {
        a[i] = static_cast<float>((i * 131) % 256);
    }

    auto start = std::chrono::high_resolution_clock::now();

    for (int p = 0; p < P; p++)
    {
#pragma omp parallel for schedule(static) default(none) shared(a, b, N)
        for (int y = 1; y < N - 1; y++)
        {
#pragma omp simd
            for (int x = 1; x < N - 1; x++)
            {
                float s = 0.0f;
                for (int dy = -1; dy <= 1; dy++)
                {
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        s += a[(y + dy) * N + (x + dx)];
                    }
                }
                b[y * N + x] = s / 9.0f;
            }
        }
        a.swap(b);
    }

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> diff = end - start;

    double checksum = 0.0;
    for (int i = 0; i < N * N; i++)
    {
        checksum += a[i];
    }

    std::printf("N=%d passes=%d  checksum=%.2f  tempo=%.6f s\n", N, P, checksum, diff.count());

    return 0;
}