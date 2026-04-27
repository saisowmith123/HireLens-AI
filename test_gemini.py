import google.generativeai as genai

# Your Gemini API key (testing only)
genai.configure(api_key="AIzaSyBJoskLvMwbX5uUWhkD1KeJVjcnyqDrlew")

try:
    model = genai.GenerativeModel("models/gemini-pro")
    chat = model.start_chat()
    response = chat.send_message("Hello Gemini! Are you working?")
    print(" Gemini Response:\n", response.text)
except Exception as e:
    print(" Error communicating with Gemini:\n", e)
