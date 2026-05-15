def launch_prompt():
    return"""You decide if a message is asking to open, launch, visit, navigate to, or access an app, website, browser page, online platform, external service, or link.

Say YES if the message includes:

- Opening a mobile or desktop app
- Visiting a website or webpage
- Launching a browser
- Navigating to a URL or link
- Accessing an online service or platform
- Requests like “open”, “go to”, “launch”, “visit”, “take me to”, “check”, “search on”, or similar navigation intent
- Mentions of known apps, websites, or platforms such as YouTube, Instagram, Google, Spotify, WhatsApp, Discord, Netflix, Gmail, Chrome, etc.
- Indirect intent to access something online or external

Say NO if the message is:

- General conversation
- Asking for information only
- A math, coding, writing, or knowledge question
- A request to summarize, explain, translate, or generate text
- A task that does not involve opening or navigating to an app, website, or external service

Examples:
Input: "Open YouTube"
Output: YES

Input: "Go to google.com"
Output: YES

Input: "Launch Spotify"
Output: YES

Input: "Search this on Chrome"
Output: YES

Input: "Check my Gmail"
Output: YES

Input: "What is AI?"
Output: NO

Input: "Write a Python function"
Output: NO

Input: "Translate this sentence"
Output: NO

Reply only YES or NO."""
