import datetime
import yaml
import threading
import logging
import time
from UART_communication import UARTCommunicator
from Conditional import Validator
from Statistic import ReportGenerator
from Serial_Port_Monitoring import monitor_serial_port

logging.basicConfig(level=logging.INFO, filename="process_control.log", filemode="w")


class TestRunner:
    def __init__(self, test_case_file, command_library_file, report_file):
        self.test_cases = self.load_yaml(test_case_file).get("test_cases", {})
        self.command_library = self.load_yaml(command_library_file).get("Command_Line", {})
        self.uart = UARTCommunicator()
        self.validator = Validator()
        self.report_generator = ReportGenerator(report_file)
        self.user_inputs = self.load_user_inputs("Selected_Test_Plan.yml")
        self.results = []
        self.pass_count = 0
        self.fail_count = 0

    @staticmethod
    def load_yaml(file_path):
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logging.error(f"YAML file not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file {file_path}: {e}")
            return {}

    @staticmethod
    def load_user_inputs(file_path):
        try:
            with open(file_path, "r") as file:
                data = yaml.safe_load(file)
                required_keys = ["selected_test_plan", "device_sn", "fw_version", "sw_version", "wifi_version"]
                if not all(key in data and data[key] for key in required_keys):
                    raise ValueError("Missing required keys or values in Selected_Test_Plan.yml")
                return data
        except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
            logging.error(f"Error loading user inputs: {e}")
            return None

    def run_test_case(self, test_plan):
        if test_plan not in self.test_cases:
            logging.error(f"No test cases defined for test plan: {test_plan}")
            print(f"No test cases defined for test plan: {test_plan}")
            return

        steps = self.test_cases.get(test_plan, [])
        if not steps:
            logging.error(f"No steps found for test plan: {test_plan}")
            print(f"No steps found for test plan: {test_plan}")
            return

        logging.info(f"Starting test plan: {test_plan}")
        print(f"Starting test plan: {test_plan}")

        start_time = time.time()
        for step in steps:
            for step_name, command_number in step.items():
                self.run_test_task(step_name, command_number)

        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"Test plan '{test_plan}' completed in {duration:.2f} seconds.")
        print(f"Test plan '{test_plan}' completed in {duration:.2f} seconds.")

        time.sleep(1)

    def run_test_task(self, step_name, command_number, stop_event):
        if stop_event.is_set():
           print("No response received. Stopping serial port monitoring for reinitialization.")
           logging.warning("No response received. Stopping serial port monitoring for reinitialization.")
           return
        
        command_entry = self.command_library.get(command_number)
        if not command_entry:
            logging.warning(f"Command {command_number} not found in Command_Line.yml")
            return

        command = command_entry["Command_Sends"] #The command to send via UART.
        response_expectation = command_entry["Response_Expectation"] #The expected prefix of the response (e.g., [time_tick+ok]).
        title = command_entry["Title"] #The description for test step.

        logging.info(f"Executing {step_name}: {title}")
        print(f"Executing {step_name}: {title}")

        response = self.uart.send_command(command)
        if not response:
         self.stop_event.clear()  # Clear the stop event to allow restart
         self.stop_event.set()  # Signal to stop the monitoring thread
         monitor_thread = threading.Thread(target=monitor_serial_port, args=(self.connection_event, self.stop_event))
         monitor_thread.start()
         logging.info("Serial port monitoring restarted.")
         time.sleep(1)
         return

        try:
             # Split the response into prefix and actual value
             prefix, actual_value = response.split(" ", 1)
        except ValueError:
             # If response doesn't have an actual value, treat the whole response as prefix
             prefix = response
             actual_value = ""

# First Judgement: Compare prefix with Response_Expectation
        if prefix == response_expectation:
    # Record result as "Pass" for prefix match
           logging.info(f"Prefix matched for {step_name}. Expected: {response_expectation}, Got: {prefix}")
           self.record_result(step_name, title, command, response_expectation, prefix, "Pass")
        else:
    # Record result as "Fail" for prefix mismatch
             logging.warning(f"Prefix mismatch for {step_name}. Expected: {response_expectation}, Got: {prefix}")
             self.record_result(step_name, title, command, response_expectation, prefix, "Fail")
             return  # Exit the method if prefix is incorrect

# Second Judgement: Handle the actual_value if it exists
        if actual_value:
    # Call Conditional.py to validate the actual_value
             user_condition = self.get_user_defined_condition(command_entry["ID"])
             if user_condition and self.validator.validate_value(actual_value.strip(), user_condition):
        # Record result as "Pass" for actual value validation
                logging.info(f"Actual value validated for {step_name}. Actual Value: {actual_value}, Condition: {user_condition}")
                self.record_result(step_name, title, command, response_expectation, actual_value, "Pass")
             else:
                 # Record result as "Fail" for actual value validation
                 logging.warning(f"Actual value mismatch for {step_name}. Actual Value: {actual_value}, Condition: {user_condition}")
                 self.record_result(step_name, title, command, response_expectation, actual_value, "Fail")
        time.sleep(1)

    def get_user_defined_condition(self, command_id):
        if not self.user_inputs:
            logging.error("User inputs not loaded.")
            return None

        if command_id == "Get_SN_Number":
            return {"condition": "equal", "expected": self.user_inputs.get("device_sn")}
        elif command_id == "Get_FW_Version":
            return {"condition": "equal", "expected": self.user_inputs.get("fw_version")}
        elif command_id == "Get_LCM_Version":
            return {"condition": "equal", "expected": self.user_inputs.get("sw_version")}
        elif command_id == "Get_WiFi_Version":
            return {"condition": "equal", "expected": self.user_inputs.get("wifi_version")}
        return None

    def record_result(self, step_name, title, command, response_expectation, actual_value, result):
        if result == "Pass":
            self.pass_count += 1
        else:
            self.fail_count += 1

        logging.info(f"Result for {step_name}: {result}")
        self.report_generator.add_result(step_name, title, command, response_expectation, actual_value, result)

    time.sleep(1)

def main():
    connection_event = threading.Event()
    stop_event = threading.Event() # fix:0109
    
    monitor_thread = threading.Thread(target=monitor_serial_port, args=(connection_event,stop_event)) # fix:0109
    monitor_thread.start()

    connection_event.wait()

    user_inputs = TestRunner.load_user_inputs("Selected_Test_Plan.yml")

    test_plan = user_inputs["selected_test_plan"]
    report_file = f"Test_Report_{datetime.datetime.now().strftime('%Y_%m_%d')}.txt"
    runner = TestRunner("Test_Case.yml", "Command_Line.yml", report_file)

    try:
        runner.run_test_case(test_plan, stop_event=stop_event)
    except Exception as e:
        logging.error(f"Error during test execution: {e}")
        print(f"Error: {e}")
    finally:
        connection_event.clear()
        logging.info("Serial monitoring stopped.")

    stop_event.set()
    monitor_thread.join()
    print(f"Test Completed: {test_plan}")
    logging.info(f"Test Completed: {test_plan}")


if __name__ == "__main__":
    main()
