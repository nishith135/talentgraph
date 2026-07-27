from pydantic import BaseModel, validator
from typing import Optional

class TestModel(BaseModel):
    name: str
    age: int
    score: float

# This works fine
valid = TestModel(name="Nishith", age=22, score=0.95)
print(valid)

# This fails - age should be int, not text
invalid = TestModel(name="Nishith", age="not a number", score=0.95)
print(invalid)