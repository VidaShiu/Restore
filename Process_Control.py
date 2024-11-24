import threading
import sys
import time
import yaml
import logging
import os
import datetime
from UART_Communicate import send_uart_command
from Conditional import run_comparison
import Serial_Port_Monitoring
from Statistic import write_report, get_test_environment ###檢查是連動哪一些
import global_config  # Ensures cooperation with GUI.py
from threading import Thread

# Set up logging
logging.basicConfig(filename='Raw_Record.txt', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Event for UART connection status
connection_event = threading.Event()
test_results = []  # Store results of each test item


def load_yaml(file_name):
    """Load data from a YAML file."""
    try:
        with open(file_name, 'r') as file:
            return list(yaml.safe_load_all(file))  # Load multiple documents (test case steps)
    except FileNotFoundError:
        logging.error(f"YAML file {file_name} not found.")
        sys.exit(f"YAML file {file_name} not found.")


def run_test_case(test_case_file):
    """Run the test case from the provided YAML file."""
    global test_results
    test_case_data = load_yaml(test_case_file)

    for document in test_case_data:
        test_case_name = list(document['test_cases'].keys())[0]
        test_steps = document['test_cases'][test_case_name]['steps']

        print(f"Running {test_case_name}...")
        logging.info(f"Starting test case: {test_case_name}")

        for step in test_steps:
            for key, value in step.items():
                if key.startswith('Command'):
                    print(f"Execute state: sends command: {value}")
                    logging.info(f"Execute state: sends command: {value}")
                    device_response = send_uart_command(value)
                    result = {
                        'item_name': value,
                        'expected': "Expected response",
                        'actual': device_response,
                        'status': "Pass" if device_response else "Fail",
                        'test_time': f"{time.time():.2f}s"
                    }
                    test_results.append(result)
                    continue

                elif key.startswith('Condition'):
                    print(f"Execute state: validating condition: {value}")
                    logging.info(f"Execute state: validating condition: {value}")
                    condition_result = run_comparison()
                    result = {
                        'item_name': value,
                        'expected': "Condition passed",
                        'actual': "Condition passed" if condition_result else "Condition failed",
                        'status': "Pass" if condition_result else "Fail",
                        'test_time': f"{time.time():.2f}s"
                    }
                    test_results.append(result)
                    continue

                elif key.startswith('Summary'):
                    print(f"Summary: {value}")
                    logging.info(f"Summary: {value}")
                    continue

            time.sleep(1)


def statistics():
    """Generate and write the test report."""
    test_environment = get_test_environment()
    write_report(test_environment, test_results)


if __name__ == '__main__':
    # Dynamically determine the test case file from global_config
    test_case_file = global_config.selected_test_plan.replace(' ', '_') + "_Test_Case.yml"

    # Validate test case file existence
    if not os.path.exists(test_case_file):
        print(f"Test case file {test_case_file} does not exist. Please check your selection.")
        sys.exit(1)

    # Start serial port monitoring in a separate thread
    monitor_thread = threading.Thread(target=Serial_Port_Monitoring.monitor_serial_port, args=(connection_event,))
    monitor_thread.start()

    print("Waiting for UART communication to be established...")
    connection_event.wait()
    print("UART communication established. Now running the test case.")

    # Start the selected test plan
    start_time = time.time()
    run_test_case(test_case_file)
    end_time = time.time()

    # Update test environment with accurate start and finish times
    test_environment = get_test_environment()
    test_environment['Start Time'] = datetime.datetime.fromtimestamp(start_time)
    test_environment['Finish Time'] = datetime.datetime.fromtimestamp(end_time)

    # Generate report
    write_report(test_environment, test_results)

    # Stop the serial port monitoring thread after the test case is executed
    Serial_Port_Monitoring.stop_event.set()
    monitor_thread.join()

