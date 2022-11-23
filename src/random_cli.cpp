/**
 * Command line interface around OpenABM-Covid19's random.h and its implementations.
 * Allows automated generation of values to evaluate errors and randomness of any
 * underlying implementations.
 * 
 * TODO compare outputs of both GSL and Stats options using
 * https://en.wikipedia.org/wiki/Kolmogorov%E2%80%93Smirnov_test
 */
#include "random.h"
#include <iostream>
#include <cmath>

void output_uniform(int n) {
    // Create a generator
    struct generator* gen = rng_alloc();

    // Seed it
    rng_set(gen, 4357); // legacy seed for RNG

    // Now generate a set of unifrom RNGs and calculate the mean and variance
    for (int i = 0;i < n; ++i) {
        std::cout << "uniform,,,,," << i << "," << rng_uniform(gen) << std::endl;
    }

    // Free RNG
    rng_free(gen);
}

void test_uniform() {
    // Create a generator
    struct generator* gen = rng_alloc();

    // Seed it
    rng_set(gen, 4357); // legacy seed for RNG

    // Now generate a set of unifrom RNGs and calculate the mean and variance
    const int n = 10000;
    const int divisions = 10;
    double divCounts[divisions];
    bool bucketsOk[divisions];
    for (int i = 0;i < divisions;++i) {
        divCounts[i] = 0.0;
        bucketsOk[i] = true;
    }
    double results[n];
    double total = 0;
    for (int i = 0;i < n; ++i) {
        results[i] = rng_uniform(gen);
        total += results[i];
        divCounts[(int)floor(results[i] * divisions)] += 1;
    }
    double mean = total / n;
    double vartotal = 0;
    for (int i = 0;i < n; ++i) {
        vartotal += (results[i] - mean) * (results[i] - mean);
    }
    double variance = vartotal / (n - 1);

    // ensure these are in the expected range
    bool expMean = (mean > 0.49) & (mean < 0.51);
    double uniformVariance = (1.0 / 12.0) * ((1.0 - 0.0) * (1.0 - 0.0)); // written out fully for clarity even though it simplifies
    bool expVar = (variance > (uniformVariance - 0.01)) & (variance < (uniformVariance + 0.01));
    double expBucketCounts = n / divisions;
    int minCount = expBucketCounts * 0.90;
    int maxCount = expBucketCounts * 1.10;
    for (int i = 0;i < divisions;++i) {
        bucketsOk[i] = (divCounts[i] >= minCount) & (divCounts[i] <= maxCount);
    }

    // Assert correctfulness
    std::cout << "Uniform Distribution" << std::endl;
    if (expMean) {
        std::cout << " - Mean within expected range: 0.49-0.51, actual: " << mean << std::endl;
    } else {
        std::cout << " - Mean NOT within expected range: 0.49-0.51, actual: " << mean << std::endl;
    }
    if (expVar) {
        std::cout << " - Variance within expected range: " << (uniformVariance-0.01) << "-" << (uniformVariance+0.01) << ", actual: " << variance << std::endl;
    } else {
        std::cout << " - Variance NOT within expected range: " << (uniformVariance-0.01) << "-" << (uniformVariance+0.01) << ", actual: " << variance << std::endl;
    }
    std::cout << " - Buckets OK? (All should be 1s): ";
    bool allOk = true;
    for (int i = 0;i < divisions;++i) {
        if (bucketsOk[i]) {
            std::cout << "1";
        } else {
            std::cout << "0";
            allOk = false;
        }
    }
    std::cout << std::endl;
    std::cout << " - Bucket counts (Should be between " << minCount << " and " << maxCount << " inclusive):-" << std::endl;
    for (int i = 0;i < divisions;++i) {
        std::cout << "    - Bucket " << i << " actual count: " << divCounts[i] << std::endl;
    }
    if (expMean & expVar & allOk) {
        std::cout << " - PASS" << std::endl;
    } else {
        std::cout << " - FAIL" << std::endl;
    }

    // Free RNG
    rng_free(gen);
}

void output_bernoulli(int n) {
    // Create a generator
    struct generator* gen = rng_alloc();

    double p = 0.5;
    for (int pint = 1;pint < 10;++pint) {
        p = ((double)pint) / 10.0;

        // Seed it
        rng_set(gen, 4357); // legacy seed for RNG

        // Now generate a set of unifrom RNGs and calculate the mean and variance
        for (int i = 0;i < n; ++i) {
            std::cout << "bernoulli," << p << ",,,," << i << "," << ran_bernoulli(gen,p) << std::endl;
        }
    }

    // Free RNG
    rng_free(gen);
}

void test_bernoulli() {
    // Create a generator
    struct generator* gen = rng_alloc();

    // Seed it
    rng_set(gen, 4357); // legacy seed for RNG

    const int n = 10000;
    int results[n];
    double total = 0;
    for (int i = 0;i < n; ++i) {
        results[i] = ran_bernoulli(gen,0.5);
        total += results[i];
    }
    double mean = total / n;
    double vartotal = 0;
    for (int i = 0;i < n; ++i) {
        vartotal += (results[i] - mean) * (results[i] - mean);
    }
    double variance = vartotal / (n - 1);

    // ensure these are in the expected range
    // We know for a Normal distribution, 95% of all results will be within 2 SD of the mean
    // See https://amsi.org.au/ESA_Senior_Years/SeniorTopic4/4h/4h_2content_11.html
    // 95% CI of the true mean, with 10 DoF = 1.812
    double trueMeanMin = mean - (1.812*(sqrt(variance)/sqrt(n)));
    double trueMeanMax = mean + (1.812*(sqrt(variance)/sqrt(n)));
    // bool expMean = (mean > 0.49) & (mean < 0.51);
    bool expMean = (mean > trueMeanMin) & (mean < trueMeanMax);
    // double distributionVariance = 0.5;
    // bool expVar = (variance > (distributionVariance - 0.01)) & (variance < (distributionVariance + 0.01));


    // Assert correctfulness
    std::cout << "Bernoulli Distribution" << std::endl;
    if (expMean) {
        std::cout << " - Mean within expected range: " << trueMeanMin << "-" << trueMeanMax << ", actual: " << mean << std::endl;
    } else {
        std::cout << " - Mean NOT within expected range: " << trueMeanMin << "-" << trueMeanMax << ", actual: " << mean << std::endl;
    }
    // if (expVar) {
    //     std::cout << " - Variance within expected range: " << (distributionVariance-0.01) << "-" << (distributionVariance+0.01) << ", actual: " << variance << std::endl;
    // } else {
    //     std::cout << " - Variance NOT within expected range: " << (distributionVariance-0.01) << "-" << (distributionVariance+0.01) << ", actual: " << variance << std::endl;
    // }
    if (expMean) {
        std::cout << " - PASS" << std::endl;
    } else {
        std::cout << " - FAIL" << std::endl;
    }

    // Free RNG
    rng_free(gen);
}

void output_gamma(int n) {
    // Create a generator
    struct generator* gen = rng_alloc();

    
    double a = 0.0;
    double b = 0.0;
    for (int aint = 0;aint < 10;++aint) {
        a += 0.5;
        b = 0.0;
        for (int bint = 0;bint < 10;++bint) {
            b += 0.5;

            // Seed it
            rng_set(gen, 4357); // legacy seed for RNG

            // Now generate a set of unifrom RNGs and calculate the mean and variance
            for (int i = 0;i < n; ++i) {
                std::cout << "gamma,," << a << "," << b << ",," << i << "," << ran_gamma(gen,a,b) << std::endl;
            }
        }
    }

    // Free RNG
    rng_free(gen);
}

int main(int argc, char *argv[])
{
    bool csv = false;
    int n = 10000;
    if (argc > 1) {
        csv = (0 == strcmp("csv",argv[1]));
    }
    if (csv) {
        std::cout << "distribution,p,a,b,mu,idx,result" << std::endl;
        output_uniform(n);
        output_bernoulli(n);
        output_gamma(n);
    } else {
        test_uniform();
        test_bernoulli();
    }

    return 0;
}
