import yaml
import os
from .models import ContractSpec, ContractSpecWrapper

class ContractLoadError(Exception):
    pass

def load_contract_from_yaml(file_path: str) -> ContractSpec:
    """
    Loads a YAML contract, validates it against the Pydantic ContractSpec model,
    and returns the ContractSpec object.
    
    The expected YAML format has a top-level "contract:" key.
    """
    if not os.path.exists(file_path):
        raise ContractLoadError(f"Contract file not found: {file_path}")
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
            
        if not raw_data or "contract" not in raw_data:
            raise ContractLoadError(f"Invalid contract format: Missing top-level 'contract' key in {file_path}")
            
        validated = ContractSpecWrapper(**raw_data)
        return validated.contract
        
    except Exception as e:
        raise ContractLoadError(f"Failed to load or validate contract {file_path}: {str(e)}")


# Convenience alias used throughout tests and CLI
load_contract = load_contract_from_yaml
