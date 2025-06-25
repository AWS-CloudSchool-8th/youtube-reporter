from pydantic import BaseModel
from typing import Any

class RunResponse(BaseModel):
    final_output: Any