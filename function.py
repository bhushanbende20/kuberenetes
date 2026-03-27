# function.py
import requests
import yaml
import json

def main():
    try:
        # Test both installed packages
        print("Testing requests...")
        response = requests.get('https://api.restful-api.dev/objects', timeout=5)
        
        # Test YAML (if needed)
        test_yaml = yaml.safe_load("""
        name: test
        value: 123
        """)
        
        return {
            "status": "success",
            "http_status": response.status_code,
            "response_data": response.json(),
            "yaml_test": test_yaml,
            "message": "All dependencies working!"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }