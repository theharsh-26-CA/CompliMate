# Token Oriented Object Notation (TOON) Utility
# More token-efficient format for LLM communication

def toon_encode(data, delimiter='|', separator=':'):
    """
    Encode Python dict to TOON format.
    
    Args:
        data: Dictionary to encode
        delimiter: Character to separate key-value pairs (default: |)
        separator: Character to separate keys from values (default: :)
    
    Returns:
        TOON formatted string
    
    Example:
        >>> toon_encode({'name': 'John', 'age': 30, 'active': True})
        'name:John|age:30|active:true'
    """
    pairs = []
    for key, value in data.items():
        if isinstance(value, bool):
            pairs.append(f"{key}{separator}{str(value).lower()}")
        elif isinstance(value, (int, float)):
            pairs.append(f"{key}{separator}{value}")
        elif isinstance(value, dict):
            # Nested dict: use dot notation
            nested_pairs = []
            for nkey, nvalue in value.items():
                nested_pairs.append(f"{key}.{nkey}{separator}{nvalue}")
            pairs.extend(nested_pairs)
        elif isinstance(value, list):
            # Lists: comma-separated
            list_str = ','.join(str(v) for v in value)
            pairs.append(f"{key}{separator}[{list_str}]")
        else:
            pairs.append(f"{key}{separator}{value}")
    
    return delimiter.join(pairs)

def toon_decode(toon_string, delimiter='|', separator=':'):
    """
    Decode TOON format to Python dict.
    
    Args:
        toon_string: TOON formatted string
        delimiter: Character that separates key-value pairs
        separator: Character that separates keys from values
    
    Returns:
        Python dictionary
    
    Example:
        >>> toon_decode('name:John|age:30|active:true')
        {'name': 'John', 'age': '30', 'active': True}
    """
    result = {}
    pairs = toon_string.strip().split(delimiter)
    
    for pair in pairs:
        if separator not in pair:
            continue
        
        parts = pair.split(separator, 1)  # Split only on first occurrence
        if len(parts) != 2:
            continue
        
        key, value = parts
        key = key.strip()
        value = value.strip()
        
        # Handle nested keys (dot notation)
        if '.' in key:
            base_key, sub_key = key.split('.', 1)
            if base_key not in result:
                result[base_key] = {}
            result[base_key][sub_key] = _parse_value(value)
        else:
            result[key] = _parse_value(value)
    
    return result

def _parse_value(value):
    """Parse value to appropriate Python type."""
    # Boolean
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    
    # Number
    if value.replace('.', '', 1).replace('-', '', 1).isdigit():
        return float(value) if '.' in value else int(value)
    
    # List
    if value.startswith('[') and value.endswith(']'):
        items = value[1:-1].split(',')
        return [item.strip() for item in items if item.strip()]
    
    # String (default)
    return value

def compare_formats(data):
    """
    Compare token efficiency between JSON and TOON.
    Useful for debugging and optimization.
    """
    import json
    
    json_str = json.dumps(data)
    toon_str = toon_encode(data)
    
    json_tokens = len(json_str.split())
    toon_tokens = len(toon_str.split('|'))
    
    savings = ((len(json_str) - len(toon_str)) / len(json_str)) * 100
    
    return {
        'json_length': len(json_str),
        'toon_length': len(toon_str),
        'savings_percent': round(savings, 2),
        'json_sample': json_str[:100],
        'toon_sample': toon_str[:100]
    }

# Example usage
if __name__ == '__main__':
    # Test TOON encoding/decoding
    test_data = {
        'compliance_name': 'GST GSTR-3B',
        'new_due_date': '2024-04-25',
        'financial_year': '2023-2024',
        'is_permanent': False,
        'category': 'GST',
        'frequency': 'Monthly'
    }
    
    print("Original Data:")
    print(test_data)
    print()
    
    toon = toon_encode(test_data)
    print("TOON Format:")
    print(toon)
    print()
    
    decoded = toon_decode(toon)
    print("Decoded Data:")
    print(decoded)
    print()
    
    comparison = compare_formats(test_data)
    print("Format Comparison:")
    print(f"JSON: {comparison['json_length']} chars")
    print(f"TOON: {comparison['toon_length']} chars")
    print(f"Savings: {comparison['savings_percent']}%")
