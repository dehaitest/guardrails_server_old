from openai import OpenAI
import prompts
import json
import ast

class Chatbot():
    def __init__(self) -> None:
        self.client = OpenAI(api_key=self.get_api_key("config.json"))

        self.sysprompt = 'You are a guardrail to monitor the behavior of an AI model. You should output only the results according to the rules given to you without any explanation.'
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

    
class Pii():
    process_type = 'pre'
    description = 'Personally identifiable information'

    @staticmethod
    def rail(history):
        chatbot = Chatbot()
        chatbot.chat_history.append({"role": "system", "content": prompts.PII})
        chatbot.chat_history.append({"role": "user", "content": '[user message]: {}'.format(history[-1]['content'])})
        return json.loads(chatbot.chat())

class Topical():
    process_type = 'pre'
    description = 'Topical'

    @staticmethod
    def rail(history):
        chatbot = Chatbot()
        chatbot.chat_history.append({"role": "system", "content": prompts.topical})
        chatbot.chat_history.append({"role": "user", "content": '[instruction]: {}, [user message]: {}'.format(history[0]['content'], history[-1]['content'])})
        return json.loads(chatbot.chat())

class Consistency():
    process_type = 'post'
    description = 'Consistency'
        
    @staticmethod
    def rail(history):
        chatbot = Chatbot()
        chatbot.chat_history.append({"role": "system", "content": prompts.factuality})
        chatbot.chat_history.append({"role": "user", "content": '[instruction]: {}, [user message]: {}, [bot message]: {}'.format(history[0]['content'], history[-2]['content'], history[-1]['content'])})
        return json.loads(chatbot.chat())
    

class Factuality():
    process_type = 'post'
    description = 'Factuality'

    @staticmethod
    def rail(history):
        chatbot = Chatbot()
        chatbot.chat_history.append({"role": "system", "content": prompts.factuality})
        chatbot.chat_history.append({"role": "user", "content": '[instruction]: {}, [user message]: {}, [bot message]: {}'.format(history[0]['content'], history[-2]['content'], history[-1]['content'])})
        return json.loads(chatbot.chat())


class Toxicity():
    process_type = 'post'
    description = 'Toxicity'

    @staticmethod
    def rail(history):
        prompt = 'Is this output legal, ethical and not harmful to any person? Your response should be formatted as a dictionary and limited to a simple "yes" or "no" answer with "answer" as key.'
        chatbot = Chatbot()
        prompt = prompt + '\nContent: ' + history[-1]['content']
        chatbot.chat_history = chatbot.chat_history + [{"role": "user", "content": prompt}] 
        return history[-1]['content'] if ast.literal_eval(chatbot.chat())['answer'] == 'yes' else 'Toxic results'

class Evaluated():
    process_type = 'post'
    description = 'Evaluated AI'
    
    @staticmethod
    def rail(history):
        chatbot = Chatbot()
        chatbot.chat_history.append({"role": "system", "content": prompts.evaluated})
        chatbot.chat_history.append({"role": "user", "content": '[instruction]: {}, [user message]: {}, [bot message]: {}'.format(history[0]['content'], history[-2]['content'], history[-1]['content'])})
        return json.loads(chatbot.chat())
