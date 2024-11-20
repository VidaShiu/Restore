from datetime import datetime
import string
import yaml
import re

def load_yaml(file_name):
    """Load data from a YAML file."""
    with open(file_name, 'r') as file:
        return yaml.safe_load(file)

def write_result(result):
    """Write the comparison result (Pass/Fail) to Result.txt."""
    with open('Result.txt', 'a') as file:
        file.write(result + '\n')

# Generic comparison functions
def compare_between(value, low, high):
    """Check if the value is between the low and high limits."""
    return low <= value <= high

def compare_equal(value, expected):
    """Check if the value is equal to the expected value."""
    return value == expected

def check_length_and_type(value, expected_length, expected_type="char"):
    """Check if the value has the expected length and type."""
    if isinstance(value, str) and value.isdigit():  # Check for numeric-only characters
        return len(value) == expected_length
    return False

def transform_timestamp(device_timestamp, transformation_type="unix_to_datetime"):
    """Convert the device timestamp according to the specified transformation type."""
    if transformation_type == "unix_to_datetime":
        # Assume device_timestamp is in seconds since Unix epoch
        return datetime.fromtimestamp(int(device_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    # Add other transformation types as needed
    return device_timestamp

def validate_value(device_value, statement):
    """Validate the device value based on the condition."""
    condition = statement.get('condition')

    if condition == 'between':
        low = float(statement['low'])
        high = float(statement['high'])
        return compare_between(float(device_value), low, high)
    
    elif condition == 'equal':
        expected = float(statement['expected'])
        return compare_equal(float(device_value), expected)

    
    elif condition == 'check_length_and_type':
        expected_length = int(statement.get('expected_length', 0))
        expected_type = statement.get('expected_type', "char")
        return check_length_and_type(str(device_value), expected_length, expected_type)

    elif condition == 'timestamp':
        # Perform timestamp transformation and compare with expected
        transformation_type = statement.get('transformation_type', "unix_to_datetime")
        transformed_timestamp = transform_timestamp(device_value, transformation_type)
        expected_timestamp = statement.get('expected')
        return compare_equal(transformed_timestamp, expected_timestamp)

    return False

def is_valid_mac_address(mac_address, mac_pattern=None, valid_prefixes=None):
    """Check if the MAC address format is valid and matches any required prefixes."""
    mac_pattern = mac_pattern or r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    
    if not re.match(mac_address, mac_pattern):
        return False
    if valid_prefixes:
        # Check if MAC address starts with any of the valid prefixes
        if not any(mac_address.startswith(prefix) for prefix in valid_prefixes):
            return False
    return True

# Example usage with device-specific prefixes
device_mac = "9C:65:F9:3C:A1:9B"
device_prefixes = ["9C:65", "00:1A", "AC:DE"]

if is_valid_mac_address(device_mac, valid_prefixes=device_prefixes):
    print(f"MAC address {device_mac} is valid for the device.")
else:
    print(f"MAC address {device_mac} is invalid for the device.")

def update_pass_fail_count(is_pass):
    """Update the pass or fail count in the Result.txt file."""
    # Check if Result.txt exists and has the correct format; if not, initialize it
    try:
        with open('Result.txt', 'r+') as file:
            lines = file.readlines()
            # Initialize if the file is empty or not correctly formatted
            if len(lines) < 2 or not lines[0].startswith("Pass Time:") or not lines[1].startswith("Fail Time:"):
                lines = ["Pass Time: 0\n", "Fail Time: 0\n"]

            # Update the count based on whether it is a pass or fail
            if is_pass:
                pass_count = int(lines[0].strip().split(': ')[1]) + 1
                lines[0] = f"Pass Time: {pass_count}\n"
            else:
                fail_count = int(lines[1].strip().split(': ')[1]) + 1
                lines[1] = f"Fail Time: {fail_count}\n"
            
            # Write the updated lines back to the file
            file.seek(0)
            file.writelines(lines)

    except (FileNotFoundError, ValueError, IndexError) as e:
        # Initialize the file if not found or if any parsing error occurs
        with open('Result.txt', 'w') as file:
            file.writelines(["Pass Time: 0\n", "Fail Time: 0\n"])
            
def run_comparison():
    # Load data from Returns_Received.yml (device responses)
    returned_values = load_yaml('Returns_Received.yml')

    # Load standards from Statement.yml
    standards = load_yaml('Statement.yml')

    for key, device_value in returned_values.items():
        if key in standards:
            standard = standards[key]
            # Perform the validation
            if validate_value(device_value, standard):
                result = f"{key}: Pass, {device_value} "
                print(result)
                write_result(result)
                update_pass_fail_count(is_pass=True)
            else:
                result = f"{key}: Fail, {device_value}"
                print(result)
                write_result(result)
                update_pass_fail_count(is_pass=False)
        else:
            print(f"No standard found for {key}")
            write_result(f"{key}: No standard found")
            update_pass_fail_count(is_pass=False)

if __name__ == '__main__':
    run_comparison()