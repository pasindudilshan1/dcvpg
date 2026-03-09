import os
import glob
from typing import Dict, List
from .models import ContractSpec
from .contract_loader import load_contract_from_yaml, ContractLoadError

class ContractRegistry:
    def __init__(self, contracts_dir: str):
        self.contracts_dir = contracts_dir
        self._contracts: Dict[str, ContractSpec] = {}
        self.discover_contracts()

    def discover_contracts(self):
        """
        Scans the contracts_dir recursively for all .yaml and .yml files,
        loads them, and registers them into the internal _contracts dict.
        """
        if not os.path.exists(self.contracts_dir):
            raise FileNotFoundError(f"Contracts directory not found: {self.contracts_dir}")

        yaml_files = glob.glob(os.path.join(self.contracts_dir, "**/*.yml"), recursive=True)
        yaml_files.extend(glob.glob(os.path.join(self.contracts_dir, "**/*.yaml"), recursive=True))

        for file_path in yaml_files:
            try:
                contract = load_contract_from_yaml(file_path)
                self.register_contract(contract)
            except ContractLoadError as e:
                # Log error and continue to load others
                print(f"Failed to load contract {file_path}: {str(e)}")
            except Exception as e:
                print(f"Unexpected error loading {file_path}: {str(e)}")

    def register_contract(self, contract: ContractSpec):
        """
        Registers a single ContractSpec object into the registry.
        """
        key = contract.name
        if key in self._contracts:
            print(f"Warning: Overwriting existing contract '{key}'")
        self._contracts[key] = contract
        print(f"Registered contract: {contract.name} (v{contract.version})")

    def get_contract(self, name: str) -> ContractSpec:
        """
        Retrieves a ContractSpec by name.
        """
        if name not in self._contracts:
            raise KeyError(f"Contract '{name}' not found in registry.")
        return self._contracts[name]

    def list_contracts(self) -> List[ContractSpec]:
        """
        Lists all registered contracts.
        """
        return list(self._contracts.values())
