from flask import Flask, request, render_template
from supabase import create_client, Client
from environs import Env
import google.generativeai as genai
import os

app = Flask(__name__)
env = Env()
env.read_env()
url = env.str('SUPABASE_URL')
key = env.str('SUPABASE_KEY')
gemini_api = env.str('GEMINI_API')
genai.configure(api_key=gemini_api)
model = genai.GenerativeModel("models/gemini-1.5-pro")
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

@app.route('/gemini', methods=['POST'])
def gemini():
    print('gemini')
    data = request.get_json()
    prompt = data.get('prompt')
    print(prompt)
    response = model.generate_content(prompt)
    print(response.text)
    return {'status': 'success', 'reply': response.text}

if __name__ == '__main__':
    app.run(debug=True, port=8000)