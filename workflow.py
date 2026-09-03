import logging
from datetime import datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
def step_one(data):
    logging.info("Step 1: Validating input")
    if not data:
        raise ValueError("Input data is empty")
    return data.strip()
def step_two(data):
    logging.info("Step 2: Processing data")
    return data.upper()
def step_three(data):
    logging.info("Step 3: Saving result")
    with open(f"output_{datetime.now():%Y%m%d_%H%M%S}.txt", "w") as f:
        f.write(data)
    return True
def main_workflow(raw_input):
    try:
        result = step_one(raw_input)
        result = step_two(result)
        step_three(result)
        logging.info("Workflow completed successfully ✅")
        return True
    except Exception as e:
        logging.error(f"Workflow failed: {e}")
        return False
if __name__ == "__main__":
    main_workflow("  hello world  ")
