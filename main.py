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
# MODEL                     RPM RPD     TPM     TPD
# llama-3.1-8b-instant	    30	14,400	6,000	500,000
# llama3-70b-8192	        30	14,400	6,000	500,000
# mixtral-8x7b-32768	    30	14,400	5,000	500,000
# https://console.groq.com/keys

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
    
    grammar = data.get('grammar') or False
    context = data.get('context') or False
    examples = data.get('examples') or False

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
                context=context,
                grammar=grammar,
                examples=examples,
            )
    
    if debug:
        print('\n\nPrompt:', prompt)
        print('Model:', model, '\n\n')

    chat_completions = client2.chat.completions.create(
        messages=[
            {
                "role": "system", 
                "content": f"You are a helpful {learning} language teaching assistant. Assume that you are teaching to a {speaking} speaker! Your answers must be shorter than 150 words!" 
            },
            { 
                "role": "user",
                "content": prompt
            },
        ],
        model=model,
        # max tokens, temp, etc
    )

    answer = chat_completions.choices[0].message.content
    answer = markdown.markdown(answer)
    # if debug:
    #     print('\n\nAnswer:', answer, '\n\n')

    return jsonify({ "answer": answer })

def create_prompt(phrase, text, speaking='English', learning='Arabic', grammar=False, context=False, examples=False):
  prompt = f'Give exact translation of the phrase \'{phrase}\' in the context of the following text: \'...{text}...\''

  if context:
    prompt += f'\n\nThen give short information in {speaking} about the context in which this phrase is being used.'
    
  if grammar:
    prompt += f"\nThen give grammatical analysis of this phrase in {learning} technical/grammatical terms."
  
  if examples:
    prompt += f'\nThen give two examples of using this phrase in other {learning} sentences along with translation in {speaking}.'
    
  prompt += f'\nDo not use extra words like let me know if you need help.\nAssume I only know {speaking} so give response to the above questions using {speaking} language!'
#   {f' except when doing grammatical analysis which should be done in {learning}' if grammar else ''}
  
  return prompt

if __name__ == '__main__':
    app.run(debug=debug)