"""
Web UI integration for Business Rules transitions.

This module provides functions and utilities for integrating the Business Rules UI
with our web interface.
"""
from typing import Dict, List, Any, Optional
import json

from business_rules.fields import FIELD_NUMERIC, FIELD_TEXT, FIELD_SELECT, FIELD_NO_INPUT

from rataura2.transitions.business_rules_adapter import (
    ConversationVariables,
    TransitionActions,
    BusinessRulesTransition,
)


def get_variables_info() -> Dict[str, Any]:
    """
    Get information about available variables for the Business Rules UI.
    
    This function returns a dictionary containing information about the variables
    that can be used in Business Rules conditions. This information is used by
    the Business Rules UI to display available variables and their types.
    
    Returns:
        Dict[str, Any]: Information about available variables
    """
    # Get all methods decorated with *_rule_variable
    variables = []
    
    # Inspect the ConversationVariables class to find all rule variables
    for attr_name in dir(ConversationVariables):
        if attr_name.startswith('_'):
            continue
        
        attr = getattr(ConversationVariables, attr_name)
        if hasattr(attr, 'options'):
            # This is a select_rule_variable
            variables.append({
                'name': attr_name,
                'label': attr_name.replace('_', ' ').title(),
                'field_type': 'select',
                'options': attr.options,
            })
        elif hasattr(attr, 'rule_variable_type'):
            # This is a rule variable
            variables.append({
                'name': attr_name,
                'label': attr_name.replace('_', ' ').title(),
                'field_type': attr.rule_variable_type,
            })
    
    return {
        'variables': variables
    }


def get_actions_info() -> Dict[str, Any]:
    """
    Get information about available actions for the Business Rules UI.
    
    This function returns a dictionary containing information about the actions
    that can be triggered by Business Rules conditions. This information is used
    by the Business Rules UI to display available actions and their parameters.
    
    Returns:
        Dict[str, Any]: Information about available actions
    """
    # Get all methods decorated with rule_action
    actions = []
    
    # Inspect the TransitionActions class to find all rule actions
    for attr_name in dir(TransitionActions):
        if attr_name.startswith('_'):
            continue
        
        attr = getattr(TransitionActions, attr_name)
        if hasattr(attr, 'params'):
            # This is a rule action
            params = []
            
            # In business-rules 1.1.1, params is a list of dicts with name, label, fieldType
            for param in attr.params:
                param_info = {
                    'name': param['name'],
                    'label': param['label'],
                }
                
                # Map field types to Business Rules field types
                field_type = param['fieldType']
                if field_type == FIELD_NUMERIC:
                    param_info['field_type'] = 'numeric'
                elif field_type == FIELD_TEXT:
                    param_info['field_type'] = 'text'
                elif field_type == FIELD_SELECT:
                    param_info['field_type'] = 'select'
                elif field_type == FIELD_NO_INPUT:
                    param_info['field_type'] = 'none'
                else:
                    param_info['field_type'] = 'text'
                
                params.append(param_info)
            
            actions.append({
                'name': attr_name,
                'label': attr.label,
                'params': params,
            })
    
    return {
        'actions': actions
    }


def generate_ui_config() -> Dict[str, Any]:
    """
    Generate configuration for the Business Rules UI.
    
    This function returns a dictionary containing all the information needed
    to configure the Business Rules UI.
    
    Returns:
        Dict[str, Any]: Configuration for the Business Rules UI
    """
    variables_info = get_variables_info()
    actions_info = get_actions_info()
    
    return {
        'variables': variables_info['variables'],
        'actions': actions_info['actions'],
        'variable_type_operators': {
            'string': [
                {'name': 'equal_to', 'label': 'Equal To', 'input_type': 'text'},
                {'name': 'not_equal_to', 'label': 'Not Equal To', 'input_type': 'text'},
                {'name': 'contains', 'label': 'Contains', 'input_type': 'text'},
                {'name': 'does_not_contain', 'label': 'Does Not Contain', 'input_type': 'text'},
                {'name': 'matches_regex', 'label': 'Matches Regex', 'input_type': 'text'},
                {'name': 'is_empty', 'label': 'Is Empty', 'input_type': 'none'},
                {'name': 'is_not_empty', 'label': 'Is Not Empty', 'input_type': 'none'},
            ],
            'numeric': [
                {'name': 'equal_to', 'label': 'Equal To', 'input_type': 'numeric'},
                {'name': 'not_equal_to', 'label': 'Not Equal To', 'input_type': 'numeric'},
                {'name': 'greater_than', 'label': 'Greater Than', 'input_type': 'numeric'},
                {'name': 'less_than', 'label': 'Less Than', 'input_type': 'numeric'},
                {'name': 'greater_than_or_equal_to', 'label': 'Greater Than Or Equal To', 'input_type': 'numeric'},
                {'name': 'less_than_or_equal_to', 'label': 'Less Than Or Equal To', 'input_type': 'numeric'},
            ],
            'boolean': [
                {'name': 'is_true', 'label': 'Is True', 'input_type': 'none'},
                {'name': 'is_false', 'label': 'Is False', 'input_type': 'none'},
            ],
            'select': [
                {'name': 'equal_to', 'label': 'Equal To', 'input_type': 'select'},
                {'name': 'not_equal_to', 'label': 'Not Equal To', 'input_type': 'select'},
            ],
        }
    }


def rules_to_json(br_transition: BusinessRulesTransition) -> str:
    """
    Convert a BusinessRulesTransition to a JSON string for the UI.
    
    Args:
        br_transition: The BusinessRulesTransition to convert
        
    Returns:
        str: JSON string representation of the rules
    """
    return json.dumps(br_transition.rules_definition)


def json_to_rules(json_str: str) -> List[Dict[str, Any]]:
    """
    Convert a JSON string from the UI to a rules definition.
    
    Args:
        json_str: JSON string representation of the rules
        
    Returns:
        List[Dict[str, Any]]: Rules definition
    """
    return json.loads(json_str)

