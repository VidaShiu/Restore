# Checking and compiling the provided script for syntax and logic errors.

import serial
import threading
import os
import time
import logging
import re

# Logging configuration
logging.basicConfig(
    filename='Status_Warning.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Serial port configuration
serial_port = '/dev/ttyUSB0'
baud_rate = 115200
sends_command = "time_tick"
connected_response_pattern = r"\[time_tick\+ok\]\s*"  # RTC Response
reboot_finished = "POST Check - Coin Bat."  # Status-Reboot finished

retry_times = 5  # Maximum retries for connection
reconnect_delay = 5  # Delay before retrying
response_timeout = 10  # Response wait timeout

stop_event = threading.Event()  # Event to signal stop


def clear_terminal_buffer():
    """Clear terminal buffer to prevent residual data."""
    print("Clearing terminal buffer...")
    os.system('clear')  # Clear for Unix/Linux/macOS


def establish_uart_connection(ser, connection_event):
    """Attempt to establish UART connection with retries."""
    for attempt in range(retry_times):
        try:
            clear_terminal_buffer()
            ser.write((sends_command + '\n').encode('utf-8'))
            print(f"Sent command: {sends_command}")

            start_time = time.time()
            while time.time() - start_time < response_timeout:
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    print(f"Received: {response.strip()}")

                    if response == '>' or response == '':
                        continue

                    if re.match(connected_response_pattern, response):
                        print("UART communication successful!")
                        connection_event.set()  # Signal connection success
                        return True

            logging.info(f"Attempt {attempt + 1}/{retry_times} failed.")
            time.sleep(reconnect_delay)

        except serial.SerialException as e:
            logging.error(f"Serial communication error: {e}")
            time.sleep(reconnect_delay)

    logging.error(f"Failed to establish UART connection after {retry_times} attempts.")
    return False


def monitor_serial_port(connection_event, stop_event):
    reboot_detected = False

    while not stop_event.is_set():
        ser = None
        try:
            ser = serial.Serial(serial_port, baud_rate, timeout=1)
            print(f"Connected to {serial_port} at {baud_rate} baud rate.")
            logging.info(f"Connected to {serial_port} at {baud_rate} baud rate.")

            if establish_uart_connection(ser, connection_event):
                last_clear_time = time.time()

                while not stop_event.is_set():
                    if time.time() - last_clear_time >= 20:
                        clear_terminal_buffer()
                        last_clear_time = time.time()

                    if ser.in_waiting > 0:
                        message = ser.readline().decode('utf-8').strip()
                        print(f"Received: {message}")
                        logging.info(f"Received: {message}")

                        if reboot_finished in message:
                            print("Reboot complete detected.")
                            logging.info("Reboot complete detected.")
                            time.sleep(1)
                            reboot_detected = True

                    # Check for disconnection or device idle state
                    if not connection_event.is_set():
                        logging.info("Detected disconnection or idle. Reconnecting...")
                        break

                    time.sleep(1)

            # Reset event after disconnection
            logging.info("Reconnecting after disconnection...")
            connection_event.clear()

        except serial.SerialException as e:
            logging.error(f"Error opening serial port: {e}")
            time.sleep(reconnect_delay)

        finally:
            if ser and ser.is_open:
                ser.close()
                logging.info(f"Serial port {serial_port} closed.")
            time.sleep(reconnect_delay)


if __name__ == '__main__':
    connection_event = threading.Event()
    stop_event = threading.Event()

    monitor_thread = threading.Thread(target=monitor_serial_port, args=(connection_event, stop_event))
    monitor_thread.start()

    # Simulate stop event (for testing, replace with actual process control logic)
    time.sleep(30)  # Simulate running for 30 seconds before stopping
    stop_event.set()
    monitor_thread.join()
    logging.info("Serial port monitoring stopped.")
