#!/bin/bash

# read arguments
test_server_ip=$1
min_concurrency=$2
max_concurrency=$3

# the endpoints to test
endpoints=(echo get_price parse compute query)

# loop through each endpoint
for endpoint in "${endpoints[@]}"
do
    # loop through each level of concurrency
    for ((concurrency=min_concurrency; concurrency<=max_concurrency; concurrency*=2)) # double the concurrency for each run
    do
        echo "Running test for endpoint: $endpoint, concurrency: $concurrency"
        echo "Starting jmeter with: jmeter -n -t test_plans/${endpoint}_test_plan.jmx -l results/${test_server_ip}/${endpoint}/${concurrency}.jtl -Jtest_server_ip=${test_server_ip} -Jthread_concurrency=${concurrency}"
        jmeter -n -t test_plans/${endpoint}_test_plan.jmx -l results/${test_server_ip}/${endpoint}/${concurrency}.jtl -Jtest_server_ip=${test_server_ip} -Jthread_concurrency=${concurrency}
    done
done
