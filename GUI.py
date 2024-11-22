import tkinter as tk
from tkinter import ttk, messagebox
import yaml
import subprocess
import global_config
import os
import datetime


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GFM50-Ventilator Automatic Test Process")  # Set window title
        self.root.geometry("550x550")  # Set window geometry

        self.output_dir = '.'  # Directory to save the file
        self.output_file = self.generate_filename()

        self.dvsn_data = ""
        self.fwv_data = ""
        self.swv_data = ""
        self.wifiv_data = ""
        self.testcycle_data = ""

        # Load test plans from the Test_Plan_List.yml file
        self.test_plan_data = self.load_yaml('Test_Plan_List.yml', 'test_plans')

        # Set up GUI
        self.setup_gui()

    def setup_gui(self):
        """Set up the GUI components."""
        # Test Plan Selection
        tk.Label(self.root, text="Select A Test Plan:").grid(row=0, column=0, pady=5)
        self.test_plan_var = tk.StringVar()
        ttk.Combobox(self.root, textvariable=self.test_plan_var, values=self.test_plan_data).grid(row=0, column=1, pady=5)

        # Input Fields
        self.add_input_field("Device SN:", 1, self.dvsn_data, "dvsn_var")
        self.add_input_field("Firmware Version:", 2, self.fwv_data, "fwv_var")
        self.add_input_field("Software Version:", 3, self.swv_data, "swv_var")
        self.add_input_field("Wi-Fi Version:", 4, self.wifiv_data, "wifiv_var")
        self.add_input_field("Test Cycle:", 5, self.testcycle_data, "testcycle_var")

        # Next Button
        tk.Button(self.root, text="Next", command=self.trigger_Process_Control).grid(row=10, column=0, pady=20)

    def add_input_field(self, label, row, default_value, var_name):
        """Add a labeled input field to the GUI."""
        tk.Label(self.root, text=label).grid(row=row, column=0, pady=5)
        setattr(self, var_name, tk.StringVar(value=default_value))
        tk.Entry(self.root, textvariable=getattr(self, var_name)).grid(row=row, column=1, pady=5)

    def load_yaml(self, file_path, key):
        """Load the test plan list from a YAML file."""
        try:
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
                return data.get(key, [])
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []

    def generate_filename(self):
        """Generate the file name based on the current date."""
        current_date = datetime.datetime.now().strftime("%Y_%m_%d")
        return os.path.join(self.output_dir, f"Test_Report_{current_date}.txt")

    def ensure_file_exists(self):
        """Ensure the file exists; if not, create a new one with a header."""
        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w') as file:
                file.write("Test Report\n")
                file.write("=====================\n")  # Header for the file
            print(f"File created: {self.output_file}")
        else:
            print(f"File already exists: {self.output_file}")

    def write_data(self, dvsn_data, fwv_data, swv_data, wifiv_data, testcycle_data, test_plan_data):
        """Write test data to the output file."""
        try:
            # Ensure the file exists or create it
            self.ensure_file_exists()

            # Append the data
            with open(self.output_file, 'a') as file:
                file.write(f"Device SN: {dvsn_data}\n")
                file.write(f"FW Version: {fwv_data}\n")
                file.write(f"SW Version: {swv_data}\n")
                file.write(f"Wi-Fi Version: {wifiv_data}\n")
                file.write("\n")
                file.write("=====================\n")  # Separator between data sets
                file.write(f"Part.I-Summary\n")
                file.write(f"Test Type: {test_plan_data}\n")
                file.write(f"Test cycle: {testcycle_data}\n")

            print(f"Data written to {self.output_file}")

        except Exception as e:
            print(f"Error writing data: {e}")

    def validate_inputs(self):
        """Validate user inputs."""
        if len(self.dvsn_var.get()) != 13:
            messagebox.showerror("Validation Error", "Device SN must be exactly 13 characters long.")
            return False

        if not self.test_plan_var.get() or self.test_plan_var.get() == "Choose a Test Plan":
            messagebox.showerror("Validation Error", "Please select a valid Test Plan.")
            return False

        return True

    def trigger_Process_Control(self):
        """Validate inputs and trigger Process_Control.py."""
        if not self.validate_inputs():
            return

        selected_test_plan = self.test_plan_var.get()
        global_config.selected_test_plan = selected_test_plan
        yaml_file = f"{selected_test_plan.replace(' ', '_')}_Test_Case.yml"

        try:
            subprocess.run(["python", "Process_Control.py", yaml_file], check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Execution Error", f"Error executing Process_Control.py: {e}")
        except FileNotFoundError:
            messagebox.showerror("File Not Found", f"Test case file {yaml_file} not found.")


# Main function to run the GUI
if __name__ == '__main__':
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
