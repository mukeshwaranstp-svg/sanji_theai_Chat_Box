import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq()

SYSTEM_PROMPT = """You are Sanji, a sharp and efficient AI assistant.
You're direct, intelligent, and slightly sarcastic — like a brilliant friend, not a corporate chatbot.
Keep responses concise unless asked to elaborate."""

conversation= []

def chat(user_input):
    conversation.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}]+conversation
    )
    conversation.append({"role": "assistant", "content": response.choices[0].message.content})
    return response.choices[0].message.content
while True:
    user_input = input("you: ")
    if user_input.lower() in ["quit", "exit", "stop","bye"]:
        with open("conversation_history.txt", "w") as f:
            for message in conversation:
                f.write(f"{message['role']}: {message['content']}\n")
                f.write('_'*100 + '\n')
        print("Conversation history saved to conversation_history.txt")
        print("Sanji;Alright, if you need any help,just type hellow baddy, i will be there")
        break
    sanji_response = chat(user_input)
    print(f"sanji:{sanji_response}")