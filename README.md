# Benchmarking

This repository contains JMeter test plans, raw test results and python scripts/notebooks used in the thesis *Performance and price comparison of three popular backend frameworks and the AWS serverless stack*.

To test all endpoints at different levels of concurrency, the `test_with_levels_of_concurrency.sh` script can be used (JMeter has to be installed and you have to be in the parent directory of the `jmeter_test_plans` directory. To start a run, use e.g.:
```
./test_with_levels_of_concurrency.sh "10.0.0.12" 1 256
```
The first argument is the host/ip of the instance you want to benchmark. The second argument is the concurrency level to start at (concurrency is then doubled for every run). The third argument is the concurrency level to end at (inclusive).

The raw test results are available in `results.zip`
