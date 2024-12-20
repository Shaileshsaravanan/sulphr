from flask import Flask, request, render_template
from supabase import create_client, Client
from environs import Env
import google.generativeai as genai
from google.generativeai import upload_file, GenerativeModel
import os
import tempfile
import io
import base64
from PIL import Image

app = Flask(__name__)
env = Env()
env.read_env()
url = env.str('SUPABASE_URL')
key = env.str('SUPABASE_KEY')
gemini_api = env.str('GEMINI_API')
genai.configure(api_key=gemini_api)
model = genai.GenerativeModel("models/gemini-1.5-flash")
supabase: Client = create_client(url, key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init')
def init():
    return render_template('init.html')

@app.route('/api/gemini', methods=['POST'])
def api_gemini():
    data = request.get_json()
    prompt = data.get('prompt')
    response = model.generate_content(prompt)
    return {'response': response.text}

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

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/api/gemini/pic', methods=['POST'])
def api_gemini_pic():
    data = request.get_json()
    image = data.get('image')
    history = data.get('history')
    print(image, history)   
    
    try:
        # Decode base64 to image bytes
        image_bytes = base64.b64decode(image)
        
        # Create a temporary file to store the image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(image_bytes)
            temp_file_path = temp_file.name 
        
        # Open the image from the temporary file
        image_data = Image.open(temp_file_path)
        
        # Create a prompt for the model to process
        prompt = f"you are sulphr an online medical assistant, this is my med_history, {history}x now, can I consume this product based on my medical history? do not use user or anything, just response and maintain the conversation flow. research, search on the product and provide a response, if you are not sure, tell that due to your allrgies, you cannot consume this."
        
        # Assuming the model is designed to handle both image and text input:
        response = model.generate_content([image_data, prompt])
        
        # Print and return the response
        print(response.text)
        return {'status': 'success', 'response': response.text}
    
    except Exception as e:
        print(f"Error processing the image or generating response: {e}")
        return {'status': 'error', 'message': str(e)}

@app.route('/api/init/submit', methods=['POST'])
def api_init_submit():
    data = request.get_json()
    email = data.get('email')
    conversation = data.get('conversation')
    images = data.get('images')
    print(email, conversation)
    conversation_summary = model.generate_content(f"filter out relevant data points and provide conversation summary that can be used to assess the user's dietary restrictions and allergies, conversation: {conversation}, user's data is not relevant, and other warnings and disclaimers aren't relevant, only fetch the data points and return them.").text
    print(conversation_summary)
    prescription_summary = []
    for image in images:
        if image.startswith("data:image"):
            base64_image = image.split(",")[1]
        image_bytes = base64.b64decode(base64_image)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(image_bytes)
            temp_file_path = temp_file.name 
        #uploaded_image = upload_file(temp_file_path)
        #print(f"Uploaded file URI: {uploaded_image.uri}")
        image_data = Image.open(temp_file_path)
        prompt = "decode the prescription/medical record attached and get the relevant data points. user's data is not relevant, and other warnings and disclaimers aren't relevant, only fetch the data points and return them."
        response = model.generate_content([image_data, prompt])
        print(response.text)
        prescription_summary.append(response.text)
        print('pres done')

    final_prompt = (
        "Provide a summary of the conversation and the prescription/medical records data points. "
        "User's data is not relevant, and other warnings and disclaimers aren't relevant, "
        "only fetch the data points and return them.\n"
        f"Conversation Summary: {conversation_summary}\n"
        f"Prescription Summaries: {', '.join(prescription_summary)}"
        "reply in plain text"
    )
    response = model.generate_content(final_prompt)
    print(response.text)

    update_response = supabase.table('data').update({
        'final_summary': response.text,
        'prescription_summary': prescription_summary,
        'conversation_summary': conversation_summary
    }).eq('email', email).execute()
    print('==>', response.text)
    return {'status': 'success', 'final_summary': response.text, 'prescription_summary': prescription_summary, 'conversation_summary': conversation_summary}

if __name__ == '__main__':
    app.run(debug=True, port=8000)