import yaml
import serial
import time
import DbDumpHandler  # Import the DbDumpHandler module
import logging

# Set up logging
logging.basicConfig(filename='UART_Communicate.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load commands and responses from YAML files
def load_yaml(file_name):
    """Load data from a YAML file."""
    with open(file_name, 'r') as file:
        return yaml.safe_load(file)

command_data = load_yaml('Command.yml')
response_data = load_yaml('Response.yml')

# Retrieve commands from Command.yml
def load_commands():
    return command_data.get('commands', {})

COMMANDS = load_commands()

def write_to_yaml(data, file_name='Returns_Received.yml'):
    """Append data to Returns_Received.yml."""
    with open(file_name, 'a') as file:
        yaml.dump(data, file)

def send_uart_command(command_key):
    """Send a command to the UART device and receive the response."""
    uart_command = COMMANDS.get(command_key, {}).get("UART")
    if not uart_command:
        print(f"Command '{command_key}' not found in Command.yml")
        logging.error(f"Command '{command_key}' not found in Command.yml")
        return None

    ser = None  # Ensure ser is initialized
    try:
        ser = serial.Serial(port='/dev/ttyUSB0', baudrate=115200, timeout=1)
        ser.write(f"{uart_command}\n".encode('utf-8'))
        print(f"Sent command: {uart_command}")
        logging.info(f"Sent command: {uart_command}")
        
        time.sleep(1)  # Wait for the device to respond
        response = ser.readline().decode('utf-8').strip()
        print(f"Received response: {response}")
        logging.info(f"Received response: {response}")

        # Validate response against expected in Response.yml
        expected_response = response_data['responses'].get(command_key, {}).get('Expected', "")
        
        # Check if the response starts with the expected response part
        if response.startswith(expected_response):
            # Write the ideal response to Returns_Received.yml
            write_to_yaml({command_key: response})
            return response  # Indicate success by returning the full response
        else:
            write_to_yaml({command_key: f"Not expect response: {response}"})
            return None

    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
        logging.error(f"Serial communication error: {e}")
        return None

    finally:
        if ser and ser.is_open:
            ser.close()

def received_uart_response(response_key, actual_response):
    """Check received response against expected response and process DB dump if needed."""
    expected_response = response_data['responses'].get(response_key, {}).get('Expected')
    received_indicator = actual_response.split()[0]  # Extract '[sn_get+ok]' part from '[sn_get+ok] 1212324500026'

    # Check if the actual response matches the expected indicator
    if received_indicator == expected_response:
        write_to_yaml({response_key: actual_response})
        logging.info(f"Expected response received: {actual_response}")

        # Trigger DbDumpHandler if the response key is "db_dump"
        if response_key == "db_dump":
            try:
                DbDumpHandler.process_db_dump(actual_response)
                logging.info("DB dump processed successfully.")
                return True, "DB dump processed successfully."
            except Exception as e:
                logging.error(f"Error processing DB dump: {e}")
                return False, f"Error processing DB dump: {e}"

        # For non-db_dump responses
        return True, f"Expected response received: {actual_response}"
    else:
        logging.warning(f"Response '{actual_response}' did not match expected '{expected_response}'")
        return False, f"Response '{actual_response}' did not match expected '{expected_response}'"