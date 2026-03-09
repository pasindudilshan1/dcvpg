import importlib
import sys
import os
from typing import Type
from .base_rule import BaseRule

def load_custom_rule(class_path: str, custom_rules_dir: str = None) -> Type[BaseRule]:
    """
    Dynamically loads a custom rule class by its full module path
    (e.g., 'custom_rules.currency_rule.CurrencyValidator').
    
    Args:
        class_path (str): The dot-separated path to the rule class.
        custom_rules_dir (str, optional): The path to the custom_rules directory
                                          to add to sys.path.
    
    Returns:
        Type[BaseRule]: The loaded rule class ready to be instantiated.
        
    Raises:
        ImportError, AttributeError, ValueError
    """
    if custom_rules_dir:
        # Resolve to absolute path
        abs_custom_dir = os.path.abspath(custom_rules_dir)
        # We need the *parent* directory of `custom_rules` to be in sys.path
        # so that `import custom_rules.module_name` works.
        parent_dir = os.path.dirname(abs_custom_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            
    parts = class_path.rsplit('.', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid rule class path: '{class_path}'. Expected format 'module.submodule.ClassName'")
        
    module_name, class_name = parts
    
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_name}': {str(e)}")
        
    try:
        rule_class = getattr(module, class_name)
    except AttributeError:
        raise AttributeError(f"Class '{class_name}' not found in module '{module_name}'")
        
    if not issubclass(rule_class, BaseRule):
        raise TypeError(f"Class '{class_name}' must inherit from dcvpg.engine.rules.base_rule.BaseRule")
        
    return rule_class
