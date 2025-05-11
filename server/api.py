#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import threading
from supervisor import SupervisorAgent

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Create the supervisor agent
supervisor = SupervisorAgent()

# Function to run async code in a thread
def run_async_in_thread(async_function, *args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(async_function(*args, **kwargs))
    loop.close()
    return result

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint to handle chat messages from the frontend"""
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        # Create a thread to run the async function
        import io
        import sys
        old_stdout = sys.stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # Process the query with the supervisor agent
        result = run_async_in_thread(supervisor.route_query, user_input)
        
        # Get the captured output
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        # Return the response
        return jsonify({
            "message": output,
            "success": True
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)