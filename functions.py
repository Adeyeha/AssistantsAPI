template = {
    "type": "function",
    "function": {
      "name": "getNickname",
      "description": "Get the nickname of a city",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {"type": "string", "description": "The city and state e.g. San Francisco, CA"},
        },
        "required": ["location"]
      }
    } 
  }

reminder = {
    "type": "function",
    "function": {
      "name": "SetReminder",
      "description": "Set a reminder",
      "parameters": {
        "type": "object",
        "properties": {
          "task": {"type": "string", "description": "A short description of the task to be reminded of. e.g Prepare slides for business presentation"},
          "date": {"type": "string", "description": "The date of the reminder in MM/DD/YYYY HH24:MM:SS. e.g 03/27/2024 15:36:00"},
          "email":{"type": "string", "description": "The email of the user. e.g tupeengo@gmail.com"}    
        },
        "required": ["task","date","email"]
      }
    } 
  }


meeting = {
    "type": "function",
    "function": {
      "name": "SetupMeeting",
      "description": "Set up a meeting",
      "parameters": {
        "type": "object",
        "properties": {
          "agenda": {"type": "string", "description": "The meeting agenda. e.g To discuss the new sales strategy"},
          "date": {"type": "string", "description": "The date of the reminder in MM/DD/YYYY HH24:MM:SS. e.g 03/27/2024 15:36:00"},
          "invitee_email":{"type": "string", "description": "The email of the invited users. e.g tupeengo@gmail.com"}    
        },
        "required": ["agenda","date","invitee_email"]
      }
    } 
  }


shop = {
    "type": "function",
    "function": {
      "name": "Shop",
      "description": "Browse and shop Items o a website of choice",
      "parameters": {
        "type": "object",
        "properties": {
          "item": {"type": "string", "description": "Item to be bought or shopped. e.g A pair of sneakers"},
          "details": {"type": "string", "description": "The description of the items such as colour, texture, model, brand etc. e.g black, floffy, yeezy, 2024 model."},
          "pricecap":{"type": "string", "description": "The maximum amount to be spent for the item(s) with the currency. e.g 300 USD."},
          "website": {"type": "string", "description": "The preferred website to shop from in a url format of https://www.amazon.com."}
        },
        "required": ["item","details","pricecap","website"]
      }
    } 
}