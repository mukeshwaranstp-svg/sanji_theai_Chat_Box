def launch_prompt():
    return"""You decide if a message is EXPLICITLY asking to open, launch, or navigate to an app or website.

Say YES ONLY if the user is DIRECTLY and EXPLICITLY commanding you to open or launch something. The message MUST contain an action verb like "open", "launch", "start", "go to", "visit", "take me to", "run", or "navigate to".

Say NO if:
- The user merely MENTIONS an app or website name in conversation without asking to open it
- The user is asking ABOUT an app (e.g., "what is Spotify?", "how does YouTube work?")
- The user is talking about something they did on an app (e.g., "I saw a video on YouTube")
- The user is asking for information, help, or advice
- There is NO explicit action verb requesting to open/launch something
- The user is asking you to search for information (that's a web search, not an app launch)

Examples:
Input: "Open YouTube"
Output: YES

Input: "Launch Spotify"
Output: YES

Input: "Go to google.com"
Output: YES

Input: "I was watching YouTube yesterday"
Output: NO

Input: "What do you think about Spotify?"
Output: NO

Input: "Can you search for Python tutorials?"
Output: NO

Input: "Tell me about Chrome extensions"
Output: NO

Input: "What is AI?"
Output: NO

Input: "How is the weather today?"
Output: NO

Reply only YES or NO."""
