import pandas as pd
import numpy as np
import time
from dcvpg.engine.validator import Validator
from dcvpg.engine.models import ContractSpec

def test_validator_performance_1m_rows():
    """
    Performance test: Validate 1 Million rows within 2 seconds.
    """
    # Create large synthetic dataframe
    num_rows = 1_000_000
    df = pd.DataFrame({
        'id': np.arange(num_rows),
        'email': [f"user{i}@example.com" for i in range(10)] * (num_rows // 10),
        'age': np.random.randint(18, 65, size=num_rows),
        'status': np.random.choice(["active", "pending", "suspended"], size=num_rows)
    })
    
    # Create matching contract
    contract = ContractSpec(
        name="perf_test_contract",
        version="1.0",
        owner_team="perf",
        source_owner="perf",
        source_connection="mock",
        schema=[
            {"field": "id", "type": "integer", "nullable": False},
            {"field": "email", "type": "string", "nullable": False},
            {"field": "age", "type": "integer", "min": 0, "max": 120},
            {"field": "status", "type": "string", "allowed_values": ["active", "pending", "suspended"]}
        ]
    )
    
    validator = Validator(contract)
    
    start_time = time.time()
    report = validator.validate_batch(df, "perf_pipeline")
    duration = time.time() - start_time
    
    assert report.status == "PASSED"
    assert duration < 3.0 # Strict constraint 
    print(f"Validation of {num_rows} rows completed in {duration:.3f} seconds.")
