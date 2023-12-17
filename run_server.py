from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import openai
import json
import inspect
import guardrails
from guardrails import *
import prompts

app = Flask(__name__)
socketio = SocketIO(app)

class Chatbot_json():
    def __init__(self) -> None:
        self.client = openai.OpenAI(api_key=self.get_api_key("config.json"))
        self.chat_history = []
        
    def chat(self):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=self.chat_history,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content
    
    def get_api_key(self, config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
        return config["api_key"]

class Chatbot():
    def __init__(self) -> None:
        self.client = openai.OpenAI(api_key=self.get_api_key("config.json"))
        self.chat_history = []
        
    def chat(self):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=self.chat_history,
        )
        self.chat_history.append({"role": response.choices[0].message.role, "content": response.choices[0].message.content})
        return response.choices[0].message.content
    
    def get_api_key(self, config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
        return config["api_key"]
    
recommend_guardrails = []
other_guardrails = []
pre_list = []
post_list = []
guardrails_dict = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('send_Spl')
def handle_spl(data):
    socketio.emit('background_message', {'content': 'receive user input instruction', 'type': 'normal'})
    chatbot = Chatbot_json()
    recommend_guardrails.clear()
    other_guardrails.clear()
    guardrails_dict.clear()
    guardrail_list = [cls for _, cls in inspect.getmembers(guardrails, inspect.isclass) if cls.__module__ == "guardrails" and cls.__name__ != 'Chatbot']
    chatbot.chat_history.append({"role": "system", "content": prompts.identify_guardrails})
    chatbot.chat_history.append({"role": "user", "content": '[User description]: {}, [guardrails_list]: [{}]'.format(data.get('msg'), ', '.join([cls.__name__ for cls in guardrail_list]))})
    for cls in guardrail_list:
        guardrails_dict[cls.__name__] = cls
    socketio.emit('background_message', {'content': 'recommend guardrails', 'type': 'normal'})
    recommend_list = json.loads(chatbot.chat()).get('guardrails')
    for i in recommend_list:
        recommend_guardrails.append(guardrail_list[i])
    other_list = [rail for rail in guardrail_list if rail not in recommend_guardrails]
    for other in other_list:
        other_guardrails.append(other)
    socketio.emit('background_message', {'content': '\n', 'type': 'end'})
    return {'success': True}
    
@socketio.on('send_message')
def handle_source(data):
    chatbot = Chatbot()
    chatbot.chat_history.append({"role": "system", "content": data.get('ins', '')})
    chatbot.chat_history.append({"role": "user", "content": data.get('msg', '')})
    socketio.emit('chain_message', {'type': "input", 'content': data.get('msg', '')})
    socketio.emit('background_message', {'content': 'get user input message', 'type': 'normal'})
    for cls in pre_list:
        socketio.emit('background_message', {'content': 'run guardrails {}'.format(cls.__name__), 'type': 'normal'})
        socketio.emit('background_message', {'content': 'message input to guardrails {}'.format(chatbot.chat_history[-1].get('content', '')), 'type': 'normal'})
        socketio.emit('chain_message', {'type': "guardrails", 'content': 'run guardrails {}'.format(cls.__name__)})
        pre_result = cls.rail(chatbot.chat_history) 
        socketio.emit('background_message', {'content': 'message output by guardrails {}'.format(pre_result['content']), 'type': 'normal'})
        socketio.emit('receive_message', {'msg': 'Message processed by guardrails: {}'.format(pre_result['content'])})
        if pre_result['pass']:
            chatbot.chat_history = chatbot.chat_history[:-1] + [{"role": chatbot.chat_history[-1]["role"], "content": pre_result['content']}]
        else:
            socketio.emit('background_message', {'content': 'fail to pass guardrails {}'.format(cls.__name__), 'type': 'normal'})
            socketio.emit('chain_message', {'type': "output", 'content': '{}'.format(pre_result['content'])})
            socketio.emit('receive_message', {'msg': pre_result['content']})
            return
    socketio.emit('background_message', {'content': 'Processing message', 'type': 'normal'})
    socketio.emit('chain_message', {'type': "process", 'content': 'Processing message'})
    chatbot.chat()
    for cls in post_list:
        socketio.emit('background_message', {'content': 'run guardrails {}'.format(cls.__name__), 'type': 'normal'})
        socketio.emit('background_message', {'content': 'message input to guardrails {}'.format(chatbot.chat_history[-1].get('content', '')), 'type': 'normal'})
        socketio.emit('chain_message', {'type': "guardrails", 'content': 'Run guardrails {}'.format(cls.__name__)})
        post_result = cls.rail(chatbot.chat_history)
        socketio.emit('background_message', {'content': 'message output by guardrails {}'.format(post_result.get('content', '')), 'type': 'normal'})
        chatbot.chat_history = chatbot.chat_history[:-1] + [{"role": chatbot.chat_history[-1]["role"], "content": post_result.get('content', '')}]
    socketio.emit('background_message', {'content': 'Output result: {}'.format(chatbot.chat_history[-1].get('content', '')), 'type': 'normal'})
    socketio.emit('receive_message', {'msg': chatbot.chat_history[-1].get('content', '')})
    socketio.emit('chain_message', {'type': "output", 'content': chatbot.chat_history[-1].get('content', '')})
    socketio.emit('chain_message', {'type': "end", 'content': ''})
    socketio.emit('background_message', {'content': '\n', 'type': 'end'})

@app.route('/get-checkbox-lists')
def get_checkbox_lists():
    list1 = [cls.__name__ for cls in recommend_guardrails]
    list2 = [cls.__name__ for cls in other_guardrails]
    return jsonify({'list1': list1, 'list2': list2})

@socketio.on('add_guardrails')
def handle_guardrails(data):
    pre_list.clear()
    post_list.clear()
    # Handle the guardrails logic here
    for guardrail_name in data['selected_options']:
        if guardrails_dict[guardrail_name].process_type == 'pre':
            pre_list.append(guardrails_dict[guardrail_name])
            socketio.emit('background_message', {'content': 'Add {} to preprocessing'.format(guardrail_name), 'type': 'normal'})
        else:
            post_list.append(guardrails_dict[guardrail_name])
            socketio.emit('background_message', {'content': 'Add {} to postprocessing'.format(guardrail_name), 'type': 'normal'})


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
