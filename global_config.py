# global_config.py
# def initialize():
    selected_test_plan = "None"  # Initially, it's None

def set_test_plan(plan_name):
    global selected_test_plan
    selected_test_plan = plan_name

def get_test_plan():
    return selected_test_plan
