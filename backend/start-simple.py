from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, origins="*")

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'backend'})

@app.route('/api/quotes', methods=['GET', 'POST'])
def quotes():
    return jsonify({'status': 'success', 'quotes': []})

@app.route('/api/auth/login', methods=['POST'])
def login():
    return jsonify({'status': 'success', 'token': 'mock-token'})

@app.route('/')
def root():
    return jsonify({'service': 'MoveCRM Backend', 'version': '1.0'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
