from flask import Flask, request, render_template
from supabase import create_client, Client
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(url, key)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/init')
def init():
    return render_template('init.html')

@app.route('/api/signup', methods=['POST'])
def api_sign_up():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    response = supabase.table('data').insert({
        'email': email,
        'password': password,
        'full_name': full_name
    }).execute()
    return {'status': 'success'}

@app.route('/about')
def about():
    return 'About'

if __name__ == '__main__':
    app.run(debug=True, port=8000)