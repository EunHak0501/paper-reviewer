import re
import os
import json

from tqdm import tqdm
import google.generativeai as genai

from pipeline.utils import prompts, upload_to_gemini, wait_for_files_active
from configs.gemini_configs import extract_essentials_config

def ask_gemini_for_essentials(pdf_file_in_gemini, essential_data):
    model = genai.GenerativeModel(
        model_name=extract_essentials_config["model_name"],
        generation_config=extract_essentials_config["generation_config"],
    )

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    pdf_file_in_gemini,
                ],
            }            
        ]
    )

    prompt = prompts["extract_essentials"]["prompt"]
    response = chat_session.send_message(prompt)
    return json.loads(response.text)

def extract_essentials(pdf_file_in_gemini, essential_data):
    return ask_gemini_for_essentials(pdf_file_in_gemini, essential_data)

# Get all directories under 'articles'
article_dirs = [d for d in os.listdir('.') if os.path.isdir(os.path.join('.', d)) and re.match(r'\d{4}\.\d{5}', d)]
print(article_dirs)

# Parse essential.json for each directory
for dir_name in tqdm(article_dirs):
    pdf_file_path = f"{dir_name}/{dir_name}.pdf"
    pdf_file_in_gemini = upload_to_gemini(pdf_file_path)
    wait_for_files_active([pdf_file_in_gemini])

    essential_path = os.path.join(dir_name, 'essential.json')
    if os.path.exists(essential_path):
        with open(essential_path, 'r') as f:
            try:
                essential_data = json.load(f)
                essential_data = extract_essentials(pdf_file_in_gemini, essential_data)
                
                with open(essential_path, 'w') as f:
                    json.dump(essential_data, f)

            except json.JSONDecodeError:
                print(f"Error parsing essential.json in {dir_name}")
    else:
        print(f"No essential.json found in {dir_name}")
