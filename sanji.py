import os
import json
from groq import Groq
from dotenv import load_dotenv
from ddgs import DDGS
from datetime import datetime, timedelta, timezone

# 1. Create the timezone for IST (UTC +5:30)
ist_offset = timezone(timedelta(hours=5, minutes=30))

# 2. Get the current moment in that timezone
now = datetime.now(ist_offset)

# 3. Format it for your display
current_time = now.strftime("%B %d, %Y %H:%M:%S")
#Adjust this to your local timezone if needed


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
use date and time for the current and accurate information. If the user asks for current events, news, or anything that changes over time, you should use the web search tool to get the latest information. Always provide the most up-to-date and accurate information available.
today's date is {current_time}.


What you know about the user:
{sanji_memory}"""

SEARCH_PROMPT = "You decide if a question needs current/live information from the web. Say YES if the question is about: current events, news, who is in power, latest updates, prices, sports results, or anything that changes over time. Say NO for general knowledge. Reply only YES or NO."

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

def web_search(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results= 100)
        output =""
        for result in results:
            output += result["title"] +'\n'
            output += result["body"] +'\n''\n'
            return output
def need_web_search(user_input):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages = [{"role":"system","content":SEARCH_PROMPT},
                    {"role":"user","content":user_input}]
    )
    return "YES" in response.choices[0].message.content
while True:
    user_input = input("you: ")
    if user_input.lower() in ["quit", "exit", "stop","bye"]:
        print("Sanji;Alright, if you need any help,just type hellow baddy, i will be there")
        break
    if need_web_search(user_input):
        print("🔍 Searching web...")
        search_result = web_search(user_input)
        user_input = f" web_result:{search_result}\n\nuser question:{user_input}"

    sanji_response = chat(user_input)
    print(f"sanji:{sanji_response}")