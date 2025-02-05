# import openai
import requests
from datetime import datetime
import os
# from .constants import LANGSMITH_API_KEY

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
def post_run(run_id, name, run_type, inputs, parent_id=None):
    """Function to post a new run to the API."""
    data = {
        "id": run_id.hex,
        "name": name,
        "run_type": run_type,
        "inputs": inputs,
        "start_time": datetime.utcnow().isoformat(),
    }
    if parent_id:
        data["parent_run_id"] = parent_id.hex
    requests.post(
        "https://api.smith.langchain.com/runs",
        json=data,
        headers={"x-api-key": LANGSMITH_API_KEY}
    )

def patch_run(run_id, outputs):
    """Function to patch a run with outputs."""
    requests.patch(
        f"https://api.smith.langchain.com/runs/{run_id}",
        json={
            "outputs": outputs,
            "end_time": datetime.utcnow().isoformat(),
        },
        headers={"x-api-key": LANGSMITH_API_KEY},
    )