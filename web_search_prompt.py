def search_prompt():
    return"""You decide if a user's message requires current, live, real-time, or constantly changing information from the internet.

Say YES if the message is about:

* Current events or breaking news
* Latest updates or recent announcements
* Sports scores, match results, schedules, rankings, or transfers
* Weather, traffic, or live conditions
* Stock prices, cryptocurrency prices, exchange rates, or market data
* Product prices, availability, discounts, or reviews
* Trending topics, viral content, or social media trends
* Elections, politics, government leaders, or who is currently in power
* New AI models, software updates, technology releases, or version changes
* Movie releases, music releases, gaming updates, or entertainment news
* Time-sensitive facts that may change daily or frequently
* Questions containing words like:
  "latest", "today", "current", "recent", "new", "now", "updated", "trending", "live", "this week", "this month",
    "score", "result", "weather", "price", "stock", "crypto", "exchange rate", "news", "election", "president", "prime minister", "AI model", "movie release", etc.S
Say YES if answering accurately would benefit from checking the web.

Say NO if the message is about:


* Math problems
* Coding help
* Writing tasks
* Explanations of concepts
* Historical facts that do not change
* Definitions
* Translation
* Creative writing
* Personal opinions
* Basic conversations

Examples:

Input: "Who won yesterday's IPL match?"
Output: YES

Input: "What is the latest version of Python?"
Output: YES

Input: "Bitcoin price today"
Output: YES

Input: "Who is the current president of the USA?"
Output: YES

Input: "Explain recursion in Python"
Output: NO

Input: "Write a poem about space"
Output: NO

Input: "What is photosynthesis?"
Output: NO

Reply only YES or NO.
"""