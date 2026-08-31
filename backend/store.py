from typing import Dict
from .models import Customer, LoanApplication, Repayment

customers: Dict[int, Customer] = {}
applications: Dict[int, LoanApplication] = {}
repayments: Dict[int, Repayment] = {}

_next = {"customer": 1, "application": 1, "repayment": 1}

def next_id(kind: str) -> int:
    value = _next[kind]
    _next[kind] += 1
    return value
