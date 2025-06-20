# utils/ai_client.py
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def chat_with_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message['content']
    except Exception as e:
        print("OpenAI API error:", e)
        return "⚠️ OpenAI service error. Try again later."
