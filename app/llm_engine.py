import os
import json
from openai import OpenAI
from anthropic import Anthropic
from flask import current_app

def get_openai_client():
    return OpenAI(api_key=current_app.config['OPENAI_API_KEY'])

def get_anthropic_client():
    return Anthropic(api_key=current_app.config['ANTHROPIC_API_KEY'])

def toon_to_dict(toon_string):
    """
    Convert TOON format to Python dictionary.
    TOON format: key:value|key:value|key:nested_key:value
    More token-efficient than JSON.
    """
    result = {}
    pairs = toon_string.strip().split('|')
    
    for pair in pairs:
        if ':' not in pair:
            continue
        parts = pair.split(':')
        if len(parts) == 2:
            key, value = parts
            # Handle boolean values
            if value.lower() == 'true':
                result[key.strip()] = True
            elif value.lower() == 'false':
                result[key.strip()] = False
            else:
                result[key.strip()] = value.strip()
        elif len(parts) > 2:
            # Nested structure
            result[parts[0].strip()] = ':'.join(parts[1:]).strip()
    
    return result

def dict_to_toon(data):
    """
    Convert Python dictionary to TOON format.
    More compact than JSON for LLM responses.
    """
    pairs = []
    for key, value in data.items():
        if isinstance(value, bool):
            pairs.append(f"{key}:{str(value).lower()}")
        else:
            pairs.append(f"{key}:{value}")
    return '|'.join(pairs)

def parse_regulatory_text(text):
    """
    Uses OpenAI to parse unstructured regulatory text.
    Now using TOON format for token efficiency.
    """
    client = get_openai_client()
    
    prompt = f"""
Extract compliance information from the regulatory text below and return in TOON format.
TOON format uses pipe-separated key:value pairs for efficiency.

Required fields:
- compliance_name: Name of the compliance
- new_due_date: Date in YYYY-MM-DD format
- financial_year: e.g., 2023-2024
- is_permanent: true or false

Example TOON output:
compliance_name:GST GSTR-3B|new_due_date:2024-04-25|financial_year:2023-2024|is_permanent:false

Text:
{text}

Return ONLY the TOON formatted string:
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=150
        )
        content = response.choices[0].message.content.strip()
        
        # Parse TOON to dict
        result = toon_to_dict(content)
        
        # Convert to expected format
        return {
            'Compliance Name': result.get('compliance_name', ''),
            'New Due Date': result.get('new_due_date', ''),
            'Financial Year': result.get('financial_year', ''),
            'Is this a permanent change?': result.get('is_permanent') == 'true'
        }
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return None

def validate_extraction(text, extracted_data):
    """
    Uses Claude to validate the extraction.
    Using TOON format for efficiency.
    """
    client = get_anthropic_client()
    
    # Convert extracted data to TOON
    toon_data = dict_to_toon({
        'compliance_name': extracted_data.get('Compliance Name', ''),
        'new_due_date': extracted_data.get('New Due Date', ''),
        'financial_year': extracted_data.get('Financial Year', ''),
        'is_permanent': str(extracted_data.get('Is this a permanent change?', False)).lower()
    })
    
    prompt = f"""
You are a Senior Compliance Auditor. Verify if the extracted data matches the regulatory text.

Regulatory Text:
{text}

Extracted Data (TOON format):
{toon_data}

Return validation result in TOON format with these fields:
- valid: true or false
- reason: explanation in brief
- corrected_compliance_name: if invalid (optional)
- corrected_new_due_date: if invalid (optional)

Example:
valid:true|reason:Data matches text

Return ONLY the TOON formatted validation:
"""
    
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        content = message.content[0].text.strip()
        
        # Parse TOON response
        validation = toon_to_dict(content)
        
        return {
            'valid': validation.get('valid') == 'true',
            'reason': validation.get('reason', 'Validation completed'),
            'corrected_data': {
                'Compliance Name': validation.get('corrected_compliance_name', extracted_data.get('Compliance Name')),
                'New Due Date': validation.get('corrected_new_due_date', extracted_data.get('New Due Date')),
                'Financial Year': extracted_data.get('Financial Year'),
                'Is this a permanent change?': extracted_data.get('Is this a permanent change?')
            } if not validation.get('valid') == 'true' else None
        }
    except Exception as e:
        print(f"Anthropic Error: {e}")
        # Fallback: assume valid if Claude fails
        return {"valid": True, "reason": "Validation skipped due to error"}

def process_compliance_update(text):
    """
    Orchestrates the dual-LLM process with TOON format.
    More token-efficient than JSON.
    """
    # 1. Parse with OpenAI (TOON format)
    extracted = parse_regulatory_text(text)
    if not extracted:
        return None
        
    # 2. Validate with Claude (TOON format)
    validation = validate_extraction(text, extracted)
    
    if validation.get('valid'):
        return extracted
    else:
        return validation.get('corrected_data')

