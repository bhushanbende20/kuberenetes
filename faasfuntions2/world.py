# from flask import request

# def main():
#     """
#     Directly access query parameter 'name' from request.
#     """
#     # Flask automatically parses query parameters
#     name = request.args.get('name', 'World')
    
#     # Print the parameter
#     print(f"Name parameter: {name}")
    
#     # Print all query parameters
#     print(f"All query params: {dict(request.args)}")
    
#     return f"Hello {name} from Python in Fission 🚀"

from flask import request
import json

def main():
    """
    Handle both GET and POST requests
    """
    # Print request info for debugging
    print(f"Method: {request.method}")
    print(f"Headers: {dict(request.headers)}")
    
    # Handle GET request (your existing functionality)
    if request.method == 'GET':
        name = request.args.get('name', 'World')
        print(f"GET request with name: {name}")
        return f"Hello {name} from Python in Fission 🚀 (GET)"
    
    # Handle POST request
    elif request.method == 'POST':
        # Check content type and parse accordingly
        if request.is_json:
            data = request.get_json()
            print(f"POST JSON data: {data}")
            name = data.get('name', 'World')
            message = data.get('message', 'No message provided')
            
            return json.dumps({
                "response": f"Hello {name} from Python in Fission 🚀 (POST)",
                "your_message": message,
                "received_data": data
            }), 200, {"Content-Type": "application/json"}
        
        elif request.form:
            print(f"POST form data: {dict(request.form)}")
            name = request.form.get('name', 'World')
            return json.dumps({
                "response": f"Hello {name} from Python in Fission 🚀 (POST)",
                "received_form": dict(request.form)
            }), 200, {"Content-Type": "application/json"}
        
        else:
            # Raw data
            raw_data = request.get_data(as_text=True)
            print(f"POST raw data: {raw_data}")
            return json.dumps({
                "response": "Received raw POST data",
                "data": raw_data
            }), 200, {"Content-Type": "application/json"}
    
    # Handle other methods
    else:
        return json.dumps({
            "error": f"Method {request.method} not supported"
        }), 405, {"Content-Type": "application/json"}