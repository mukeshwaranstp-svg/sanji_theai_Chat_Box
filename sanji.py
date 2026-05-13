import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq()

def load_memory():
    if os.path.exists("sanji_memory.json"):
        with open("sanji_memory.json", "r") as f:
            sanji_memory = json.load(f)
            return sanji_memory
    else:
        return[]

sanji_memory = load_memory()

SYSTEM_PROMPT = f"""You are Sanji, a sharp and efficient AI assistant.
You're direct, intelligent, and slightly sarcastic — like a brilliant friend, not a corporate chatbot.
Keep responses concise unless asked to elaborate.

What you know about the user:
{sanji_memory}"""


conversation= []


def save_memory(sanji_memory):
    with open("sanji_memory.json", "w") as f:
        json.dump(sanji_memory, f)

def chat(user_input):
    global sanji_memory

    conversation.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}]+conversation
    )
    conversation.append({"role": "assistant", "content": response.choices[0].message.content})
    
    fact_check = client.chat.completions.create(
        model = "llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You extract personal facts about the user from their message. If there is a personal fact, return only the fact as a short sentence. If there is no personal fact, return 'none' "},
       { "role": "user", "content": user_input}]

    )
    fact = fact_check.choices[0].message.content
    if fact != "none":
        sanji_memory.append(fact)
        save_memory(sanji_memory)
    else:
        pass

    return response.choices[0].message.content


while True:
    user_input = input("you: ")
    if user_input.lower() in ["quit", "exit", "stop","bye"]:
        print("Sanji;Alright, if you need any help,just type hellow baddy, i will be there")
        break

    sanji_response = chat(user_input)
    print(f"sanji:{sanji_response}")