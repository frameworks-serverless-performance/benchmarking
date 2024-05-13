# Functions for parsing the results of the tests and calculating the average response time, standard deviation of the
# response time and requests per second. The results are returned as a pandas DataFrame.

import pandas as pd
import os
import json


def get_test_results(path_to_results_folder):
    test_results = pd.DataFrame(
        columns=['framework', 'endpoint', 'concurrency', 'requests_per_second', 'avg_response_time',
                 'max_response_time', 'response_time_standard_deviation'])
    for folder in os.listdir(path_to_results_folder):
        if os.path.isdir(os.path.join(path_to_results_folder, folder)):
            path_to_framework_folder = os.path.join(path_to_results_folder, folder)
            test_results_per_endpoint = get_test_results_of_framework(path_to_framework_folder)
            test_results_per_endpoint['framework'] = folder
            test_results = pd.concat([test_results, test_results_per_endpoint], ignore_index=True)
    return test_results


def get_test_results_of_framework(path_to_framework_folder):
    test_results_per_endpoint = pd.DataFrame(
        columns=['endpoint', 'concurrency', 'requests_per_second', 'avg_response_time', 'max_response_time',
                 'response_time_standard_deviation'])
    for folder in os.listdir(path_to_framework_folder):
        if os.path.isdir(os.path.join(path_to_framework_folder, folder)):
            path_to_endpoint_folder = os.path.join(path_to_framework_folder, folder)
            test_results_per_concurrency = get_test_results_of_endpoint(path_to_endpoint_folder, folder)
            test_results_per_concurrency['endpoint'] = folder
            test_results_per_endpoint = pd.concat([test_results_per_endpoint, test_results_per_concurrency],
                                                  ignore_index=True)
    return test_results_per_endpoint


def get_test_results_of_endpoint(path_to_endpoint_folder, endpoint_name):
    test_results_per_concurrency = pd.DataFrame(
        columns=['concurrency', 'requests_per_second', 'avg_response_time', 'max_response_time',
                 'response_time_standard_deviation'])
    for file in os.listdir(path_to_endpoint_folder):
        if file.endswith(".jtl"):
            file_path = os.path.join(path_to_endpoint_folder, file)
            concurrency = int(file.replace('.jtl', ''))
            individual_test_result = IndividualTestResult(file_path, endpoint_name)
            test_results_per_concurrency = pd.concat([test_results_per_concurrency, pd.DataFrame([[concurrency, individual_test_result.requests_per_second, individual_test_result.avg_response_time, individual_test_result.max_response_time, individual_test_result.response_time_standard_deviation]],
                                                     columns=['concurrency',
                                                              'requests_per_second',
                                                              'avg_response_time',
                                                              'max_response_time',
                                                              'response_time_standard_deviation'])],
                                                     ignore_index=True)

    return test_results_per_concurrency


class IndividualTestResult:
    def __init__(self, file_path, endpoint_name):
        self.avg_response_time = -1
        self.max_response_time = -1
        self.response_time_standard_deviation = -1
        self.requests_per_second = -1
        self.file_path = file_path
        self.endpoint_name = endpoint_name
        self.df = results_to_df(file_path)
        if not self.check_responses():
            raise ValueError("At least one of the responses did not match the expected response")
        self.calculate()

    def calculate(self):
        # we get the timestamp of the first request
        first_request = self.df['timestamp'].min()

        # we calculate the relative timestamp since the start of the test
        self.df.loc[:, 'timestamp_relative_start'] = self.df['timestamp'] - first_request

        # we calculate the relative timestamp of when the request is done
        self.df.loc[:, 'timestamp_relative_done'] = self.df['timestamp_relative_start'] + self.df['response_time_ms']

        # we remove the first 15 seconds of the test (10s thread ramp-up time + 5s warm-up time)
        # we use the done timestamp for this since we also use the done timestamp to cut off the results at the end
        self.df = self.df[self.df['timestamp_relative_done'] > 15000]

        # we remove any request that returned after the 30s mark
        self.df = self.df[self.df['timestamp_relative_done'] <= 30000]

        # now we end up with all requests that were returned between 15s and 30s

        # we calculate the average response time
        self.avg_response_time = self.df['response_time_ms'].mean()

        # we calculate the max response time
        self.max_response_time = self.df['response_time_ms'].max()

        # we calculate the standard deviation of the response time
        self.response_time_standard_deviation = self.df['response_time_ms'].std()

        # we calculate the number of requests per second
        self.requests_per_second = len(self.df) / 15

    def check_responses(self):
        # first we check that all response codes are 200 OK
        response_codes = self.df['response_code'].unique()
        if len(response_codes) > 1:
            print(f"Response codes for {self.endpoint_name} are not all 200 OK")
            print(response_codes)
        else:
            print(f"Response codes for {self.endpoint_name} are all 200 OK")

        response_data = self.df['response_data'].unique()

        if len(response_data) > 1:
            print(f"Response data for {self.endpoint_name} is not consistent")
            print(response_data)
            return False

        if self.endpoint_name == 'echo':
            if not validate_echo_response(response_data[0]):
                print(f"Response data for {self.endpoint_name} is not correct")
                print(response_data)
                return False
            print(f"Response data for {self.endpoint_name} is correct")
            return True

        if self.endpoint_name == 'get_price':
            if not validate_get_price_response(response_data[0]):
                print(f"Response data for {self.endpoint_name} is not correct")
                print(response_data)
                return False
            print(f"Response data for {self.endpoint_name} is correct")
            return True

        if self.endpoint_name == 'compute':
            if not validate_compute_response(response_data[0]):
                print(f"Response data for {self.endpoint_name} is not correct")
                print(response_data)
                return False
            print(f"Response data for {self.endpoint_name} is correct")
            return True

        if self.endpoint_name == 'parse':
            if not validate_parse_response(response_data[0]):
                print(f"Response data for {self.endpoint_name} is not correct")
                print(response_data)
                return False
            print(f"Response data for {self.endpoint_name} is correct")
            return True

        if self.endpoint_name == 'query':
            if not validate_query_response(response_data[0]):
                print(f"Response data for {self.endpoint_name} is not correct")
                print(response_data)
                return False
            print(f"Response data for {self.endpoint_name} is correct")
            return True

        print("Invalid endpoint name!")
        return False


def results_to_df(file_path):
    df = pd.read_xml(file_path)
    # t = "elapsed time in milliseconds" -> this is also called response time
    df = df.rename(columns={'t': 'response_time_ms'})
    # it = idle time -> should always be zero for our testing
    df = df.rename(columns={'it': 'idle_time_ms'})
    # lt = latency -> time to initial response in milliseconds
    df = df.rename(columns={'lt': 'latency_ms'})
    # ct = connect time -> time to establish connection in milliseconds
    df = df.rename(columns={'ct': 'connect_time_ms'})
    # ts = timestamp -> unix timestamp in milliseconds of when the request was sent
    df = df.rename(columns={'ts': 'timestamp'})
    # s = success
    df = df.rename(columns={'s': 'success'})
    # rc = response code
    df = df.rename(columns={'rc': 'response_code'})
    # rm = response message -> we don't need this
    df = df = df.drop(columns=['rm'])
    # ng = number of active threads in the group -> we don't need this since we only have one group
    df = df.drop(columns=['ng'])
    # na = number of active threads in all groups
    df = df.rename(columns={'na': 'active_threads'})
    # responseData
    df = df.rename(columns={'responseData': 'response_data'})
    return df


def validate_echo_response(response):
    if response == 'test':
        return True
    return False


def validate_get_price_response(response):
    expected_response = {
        "itemId": "73eebcb6-a5d8-46ff-8a5e-0b9e79be1489",
        "quantity": 2,
        "perItemPrice": 250,
        "totalPricePreTax": 500,
        "taxRate": 0.2,
        "totalPriceWithTax": 600
    }
    response = json.loads(response)
    if response == expected_response:
        return True
    return False


def validate_compute_response(response):
    if response == 'f79f064b519bfb1197b5c0f2e0c03c54e52fada9b850d681f7dd305f047ea1bb':
        return True
    return False


def validate_parse_response(response):
    if response == 99:
        return True
    return False


def validate_query_response(response):
    if response == 200:
        return True
