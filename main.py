from flask import Flask, request, jsonify
import json
from uuid import uuid4
from datetime import datetime
import os
import openai

app = Flask(__name__)

with open('agent.json') as f:
    agent_card = json.load(f)

tasks = {}

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def summarize_text(text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Summarize the following text in 1-2 sentences."},
            {"role": "user", "content": text}
        ],
        max_tokens=100,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()

@app.route('/.well-known/agent.json')
def get_agent_card():
    return jsonify(agent_card)

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or data.get('capability') != 'summarize' or 'text' not in data.get('input', {}):
        return jsonify({'error': 'Invalid capability or input'}), 400
    task_id = str(uuid4())
    now = datetime.utcnow().isoformat() + 'Z'
    try:
        summary = summarize_text(data['input']['text'])
    except Exception as e:
        return jsonify({'error': f'LLM error: {e}'}), 500
    task = {
        'id': task_id,
        'status': 'completed',
        'capability': 'summarize',
        'input': data['input'],
        'output': {'summary': summary},
        'createdAt': now,
        'updatedAt': now
    }
    tasks[task_id] = task
    return jsonify({'task': task}), 201

@app.route('/tasks/<task_id>')
def get_task(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify({'task': task})

if __name__ == '__main__':
    app.run(port=8000) 