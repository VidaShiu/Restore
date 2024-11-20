import datetime
import yaml

def write_report(test_environment, test_results, report_file='Test_Report.txt'):
    """Generate a test report with the given test environment and results."""

    # Part A calculations
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result['status'] == 'Pass')
    failed_tests = total_tests - passed_tests
    pass_probability = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    test_cycle = 1  # For example, change if more cycles are run

    # Calculate total test duration as human-readable format
    start_time = test_environment['Start Time']
    finish_time = test_environment['Finish Time']
    duration = str(finish_time - start_time)

    # Format start and finish times
    test_environment['Start Time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
    test_environment['Finish Time'] = finish_time.strftime("%Y-%m-%d %H:%M:%S")

    # Prepare Part B results
    part_b_passed_items = []
    part_b_failed_items = []
    for result in test_results:
        item = {
            'item_name': result['item_name'],
            'expected_value': result['expected'],
            'actual_value': result['actual'],
            'test_time': result['test_time']
        }
        if result['status'] == 'Pass':
            part_b_passed_items.append(item)
        else:
            part_b_failed_items.append(item)

    # Write report
    with open(report_file, 'w') as file:
        # Test Environment
        file.write("Test Environment:\n")
        for key, value in test_environment.items():
            file.write(f"  {key}: {value}\n")
        file.write("\n")

        # Part A Summary
        file.write("Part A: Summary\n")
        file.write(f"  Total Test Items: {total_tests}\n")
        file.write(f"  Passed Items: {passed_tests}\n")
        file.write(f"  Failed Items: {failed_tests}\n")
        file.write(f"  Pass Probability: {pass_probability:.2f}%\n")
        file.write(f"  Test Cycle: {test_cycle}\n")
        file.write(f"  Total Test Duration: {duration}\n")
        file.write("\n")

        # Part B Detailed Results
        file.write("Part B: Detailed Results\n")
        file.write("  Passed Items:\n")
        for item in part_b_passed_items:
            file.write(f"    Item Name: {item['item_name']}, Expected: {item['expected_value']}, "
                       f"Actual: {item['actual_value']}, Test Time: {item['test_time']}\n")

        file.write("\n  Failed Items:\n")
        for item in part_b_failed_items:
            file.write(f"    Item Name: {item['item_name']}, Expected: {item['expected_value']}, "
                       f"Actual: {item['actual_value']}, Test Time: {item['test_time']}\n")

    print(f"Report written to {report_file}")

def get_test_environment():
    """Retrieve test environment details like device versions and timestamps."""
    return {
        "Device SN": "1212324500026",
        "FW Version": "1.0.236",
        "SW Version": "1.0.7",
        "Wi-Fi Version": "1.0.19",
        "Start Time": datetime.datetime.now(),
        "Finish Time": datetime.datetime.now() + datetime.timedelta(minutes=5)
    }