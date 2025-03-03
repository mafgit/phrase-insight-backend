# pip install flask groq python-dotenv flask-cors
# todo: add database
from flask import Flask, request, jsonify
from groq import Groq
import os
from dotenv import load_dotenv
from flask_cors import CORS
import markdown

app = Flask(__name__)
CORS(app)

load_dotenv()
debug = os.getenv('FLASK_DEBUG') == 'TRUE'
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
client1 = Groq(api_key=GROQ_API_KEY)
# MODEL                           RPM   RPD       TPM     TPD
# llama-3.1-8b-instant	          30    14,400	  6,000	  500,000
# llama3-70b-8192	                30	  14,400	  6,000	  500,000
# mixtral-8x7b-32768	            30	  14,400	  5,000 	500,000
# mistral-saba-24b	              30	  1,000     6,000	  500,000
# deepseek-r1-distill-llama-70b	  30	  1,000	    6,000	  (No limit)
# gemma2-9b-it	                  30	  14,400	  15,000  500,000
# llama-3.3-70b-versatile	        30  	1,000 	  6,000	  100,000
# https://console.groq.com/keys

settings = {
  "translation": {"temperature": 0.2, "max_completion_tokens": 100},
  "grammar": {"temperature": 0.2, "max_completion_tokens": 250},
  "context": {"temperature": 0.3, "max_completion_tokens": 150},
  "examples": {"temperature": 0.5, "max_completion_tokens": 100},
}

@app.route('/', methods=['GET'])
def welcome():
    return jsonify({ "message": "Welcome to PhraseInsight API!" })

@app.route('/explain', methods=['POST'])
def chat():
    data = request.get_json()

    phrase = data.get('phrase') or ''
    text = data.get('text') or ''
    phrase = phrase.strip()
    text = text.strip()
    
    speaking = data.get('speaking')
    learning = data.get('learning')
    
    request_type = data.get('request_type') or 'translation'

    apikey = data.get('apikey')

    model = data.get('model') or 'llama3-70b-8192'

    if not data or not phrase or not text or not speaking or not learning or phrase.strip() == '' or text.strip() == '':
        return jsonify({ "error": "Phrase and text not provided" }), 400

    if apikey:
      client2 = Groq(api_key=apikey)
    else:
      client2 = client1

    text = text[0:270]

    prompt = create_prompt(
            phrase,
            text,
            speaking=speaking,
            learning=learning,
            request_type=request_type
          )
    

    if debug:
        print('\n\nPrompt:', prompt)
        print('Model:', model, '\n\n')

    chat_completions = client2.chat.completions.create(
        messages=[
            {
                "role": "system", 
                "content": prompt
            }
        ],
        model=model,
        temperature=settings[request_type]['temperature'],
        max_completion_tokens=settings[request_type]['max_completion_tokens'],
        frequency_penalty=0.2
    )

    answer = chat_completions.choices[0].message.content
    if debug:
        print('\n\nAnswer:', answer, '\n\n')
    answer = markdown.markdown(answer)

    return jsonify({ "answer": answer })

def create_prompt(phrase, text, speaking='English', learning='Arabic', request_type='translation'):
  prompt = f"""
User speaks: {speaking}
User is learning: {learning}
Context: "...{text}..."
"""

  if request_type == 'translation':
    prompt += f'\nProvide only the exact translation and pronunciation of phrase in {speaking}.'
  elif request_type == 'grammar':
    prompt += f'\nGive very concise grammar and structure analysis of just the phrase in {learning}. Give plural/singular if noun and past/present form if verb too.'
  elif request_type == 'context':
    prompt += f'\nGive brief contextual explanation of phrase in {speaking}.'
  elif request_type == 'examples':
    prompt += f'\nProvide two other example sentences in {learning} along with translation in {speaking}.'
  else:
    raise ValueError(f"Invalid request type: {request_type}")

  return prompt

if __name__ == '__main__':
    app.run(debug=debug)