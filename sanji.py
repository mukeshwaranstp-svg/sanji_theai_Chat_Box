import os
import json
import webbrowser
import subprocess
from web_search_prompt import search_prompt
from launch_app_prompt import launch_prompt
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

SEARCH_PROMPT = search_prompt()

LAUNCH_PROMPT = launch_prompt()

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


conversation= []


def save_memory(sanji_memory):
    with open("sanji_memory.json", "w") as f:
        json.dump(sanji_memory, f)

def chat(user_input):
    global sanji_memory

    conversation.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}]+conversation
    )
    conversation.append({"role": "assistant", "content": response.choices[0].message.content})

    fact_check = client.chat.completions.create(
        model="llama-3.1-8b-instant",
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
        results = ddgs.text(query, max_results= 20)
        output =""
        for result in results:
            output += result["title"] +'\n'
            output += result["body"] +'\n''\n'
        return output
def need_web_search(user_input):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages = [{"role":"system","content":SEARCH_PROMPT},
                    {"role":"user","content":user_input}]
    )
    return "YES" in response.choices[0].message.content

def detect (user_input):
    response = client.chat.completions.create(
       model="llama-3.1-8b-instant",
        messages = [ {
                       "role":"system","content":"""You are an app launcher assistant.
If the user wants to open a WEBSITE → reply with just the full URL. Example: https://youtube.com
If the user wants to search something on YouTube → reply with the full search URL. Example: https://www.youtube.com/results?search_query=jk+video
If the user wants to open a DESKTOP APP → reply with just the app exe name. Example: spotify, notepad, code
Reply with ONLY the URL or app name. Nothing else."""},
        {"role": "user","content": user_input}
     ]
    )
    return response.choices[0].message.content.strip()

def need_launch_app(user_input):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages = [ {
                       "role":"system","content":LAUNCH_PROMPT},
        {"role": "user","content": user_input}
     ]
    )
    return "YES" in response.choices[0].message.content

def launch_app(app_info):
    if app_info.startswith("http"):
        webbrowser.open(app_info)
    else:
        subprocess.Popen(app_info)

while True:
    user_input = input("you: ")
    if user_input.lower() in ["quit", "exit", "stop","bye"]:
        print("Sanji;Alright, if you need any help,just type hellow baddy, i will be there")
        break
    elif need_launch_app(user_input):      # check app FIRST
        print("🚀 Launching...")
        app_info = detect(user_input)
        launch_app(app_info)

    elif need_web_search(user_input):    # then web search
        print("🔍 Searching web...")
        search_result = web_search(user_input)
        user_input = f"web_result:{search_result}\n\nuser question:{user_input}"
        sanji_response = chat(user_input)
        print(f"sanji:{sanji_response}")

    else:
        sanji_response = chat(user_input)
        print(f"sanji:{sanji_response}")