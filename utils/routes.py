import os
import json
import time
import re
import hashlib
from datetime import datetime as dt, timezone
from flask import Blueprint, request, jsonify, session
from dateutil import parser
from utils.prokerala import get_access_token, get_lagna_chart, get_dasha_periods
from utils.kundali import get_planet_positions_from_data_ws, kundali_svg_to_text
from utils.prompts import build_svg_prompt, build_marriage_prompt, build_default_prompt
from utils.extractor import extract_birth_details
from utils.ai_client import chat_with_openai
from utils.cleaner import delete_file_later
from transformers import AutoTokenizer, AutoModelForCausalLM, GPT2Tokenizer, GPT2LMHeadModel, pipeline
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

CHART_DIR = "charts"
EXPIRE_SECONDS = 1620
chart_file = ''
astrology_bp = Blueprint('astrology', __name__)
USER_CACHE = {}

def format_kundli_info(chart_data):
    kundli = chart_data.get("chart_svg", {})
    info = []

    for house_number in sorted(kundli, key=lambda x: int(x)):
        item = kundli[house_number]
        house = item["house"]
        rashi = item["rashi_no"]
        planets = ", ".join(item.get("planets", [])) or "None"
        info.append(f"House {house} (Rashi {rashi}): {planets}")

    return "\n".join(info)

def find_planet_position(chart_data, planet_code):
    for house_info in chart_data.values():
        if planet_code in house_info.get("planets", []):
            return house_info["house"], house_info["rashi_no"]
    return None, None

@astrology_bp.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_input = request.json.get('question')
    user_ip = request.remote_addr or '127.0.0.1'  # fallback for localhost testing
    birth_details = extract_birth_details(user_input)

    # print("📥 Extracted Birth Details:", birth_details)
    if birth_details:
        hash_input = f"{birth_details['year']}-{birth_details['month']}-{birth_details['day']}-{birth_details['hour']}-{birth_details['minute']}-{birth_details['city']}"
        chart_hash = hashlib.md5(hash_input.encode()).hexdigest()
        chart_file = os.path.join(CHART_DIR, f"{chart_hash}.json")
        USER_CACHE[user_ip] = chart_file  # ✅ Store for IP reuse
        planet_data = get_planet_positions_from_data_ws(**birth_details, output_file=chart_file)

        if 'error' in planet_data:
            return jsonify({"message": "❌ कुंडली चार्ट नहीं मिल पाया।", "error": planet_data['error']}), 400

        kundali_text = kundali_svg_to_text(planet_data['svg'])
        # session['kundali_svg_text'] = kundali_text

        return jsonify({
            "message": "🪐 आपकी कुंडली तैयार है। आप मुझसे अब प्रश्न पूछ सकते हैं, जैसे: मेरी शादी कब होगी?",
            "svg": planet_data['svg'],
            "planet_position":planet_data['planet_position']
        })

    chart_file = USER_CACHE.get(user_ip)
    if chart_file and os.path.exists(chart_file):
        with open(chart_file, "r") as f:
            chart_data = json.load(f)
        chart_svg = chart_data.get("chart_svg", {})
        chart_s_planet_position = chart_data.get("planet_position", {})
        summary = {}

        # Load fine-tuned model
        for house, details in chart_svg.items():
            summary[house] = {
                "house": details.get("house"),
                "rashi_no": details.get("rashi_no"),
                "planets": details.get("planets")
            }

        model_path = "./model_output/t/final"
        tokenizer = GPT2Tokenizer.from_pretrained(model_path)
        model = GPT2LMHeadModel.from_pretrained(model_path)

        tokenizer.pad_token = tokenizer.eos_token
        chatbot = pipeline("text-generation", model=model, tokenizer=tokenizer)

        # Create pipeline
        # chatbot = pipeline("text-generation", model=model, tokenizer=tokenizer)

        # User se input lena
        # user_input = input("User: ")

        # Prompt format as trained
        # chart_file = data.get("chart_file", "").strip()
        # print(chart_data)
        # 🌌 Planet name to code mapping
        planet_mapping = {
            "surya": "Su", "sun": "Su",
            "chandra": "Mo", "moon": "Mo",
            "mangal": "Ma", "mars": "Ma",
            "budh": "Me", "mercury": "Me",
            "guru": "Ju", "brihaspati": "Ju", "jupiter": "Ju",
            "shukra": "Ve", "venus": "Ve",
            "shani": "Sa", "saturn": "Sa",
            "rahu": "Ra", "ketu": "Ke",
            "ascendant": "Asc", "lagna": "Asc"
        }

        # 🌠 Rashi name mapping (for Hindi to number)
        rashi_name_map = {
            "mesh": "1", "vrishabh": "2", "mithun": "3", "kark": "4", "singh": "5",
            "kanya": "6", "tula": "7", "vrishchik": "8", "dhanu": "9",
            "makar": "10", "kumbh": "11", "meen": "12"
        }

        # ✅ Format user prompt with kundli
        kundli_text = format_kundli_info(chart_data)
        user_query_lower = user_input.lower()

        # # 🔍 1. Check for Planet Position (e.g. "Mangal kaha hai")
        # for name, code in planet_mapping.items():
        #     if name in user_query_lower and "kaha" in user_query_lower:
        #         # house, rashi = find_planet_position(chart_data, code)
        #         house, rashi = find_planet_position(chart_data["chart_svg"], code)
        #         if house:
        #             bot_reply = f"{name.capitalize()} aapki kundli ke {house}th house (Rashi {rashi}) me sthit hai."
        #         else:
        #             bot_reply = f"Kundli me {name.capitalize()} ki sthaapna nahi mil rahi hai."
        #         return jsonify({"message": bot_reply})

        # # 🔍 2. Check for Rashi position (e.g. "Rashi 5 kaha hai")
        # # rashi_match = re.search(r"rashi\\s*(\\d+)", user_query_lower)
        # rashi_match = re.search(r"rashi\s*(\d+)", user_query_lower)


        # rashi_number = None
        # if not rashi_match:
        #     for name, num in rashi_name_map.items():
        #         if name in user_query_lower:
        #             rashi_number = num
        #             break
        # else:
        #     rashi_number = rashi_match.group(1)

        # if rashi_number:
        #     for house_info in chart_data["chart_svg"].values():
        #         if str(house_info.get("rashi_no")) == rashi_number:
        #             bot_reply = f"Rashi {rashi_number} aapki kundli ke {house_info['house']}th house me sthit hai."
        #             return jsonify({"message": bot_reply})

        # # 🔍 3. Check for House info (e.g. "5th house me kya hai")
        # # house_match = re.search(r"(\\d+)(st|nd|rd|th)?\\s*house", user_query_lower)
        # house_match = re.search(r"(\d+)(st|nd|rd|th)?\s*house", user_query_lower)
        # if house_match:
        #     house_number = int(house_match.group(1))
        #     for house_info in chart_data["chart_svg"].values():
        #         if int(house_info.get("house")) == house_number:
        #             rashi = house_info.get("rashi_no")
        #             planets = ", ".join(house_info.get("planets", [])) or "koi grah nahi"
        #             bot_reply = f"{house_number}th house me Rashi {rashi} sthit hai aur yaha ye grah hai: {planets}."
        #             return jsonify({"message": bot_reply})

        # 🤖 AI BASED fallback

        # chart_s_planet_position
        pdf_folder = f"data/boat"
        loader = DirectoryLoader(pdf_folder, glob="*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()
        embedding = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        vectorstore = FAISS.from_documents(documents, embedding)
        qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-4", openai_api_key=os.getenv("OPENAI_API_KEY")),
        retriever=vectorstore.as_retriever(),
        )

        # prompt = f"""User Kundli: {kundli_text}
        # User: {user_input}
        # Bot:"""

        # result = chatbot(prompt, max_length=200, do_sample=True, temperature=0.7)
        # response_text = result[0]["generated_text"]
        # print(response_text)
        # bot_reply = response_text.split("Bot:")[-1].strip()


        # 4️⃣ Query with kundli context + user question
        # user_question = "Shani ki mahadasha me kya samasya aa sakti hai?"
        final_query = f"""
        User Kundli Data:
        {kundli_text}

        User Planet Position Data:
        {chart_s_planet_position}

        User Question:
        {user_input}

        Please use the above kundli info + PDFs to give a detailed astrological answer.
        """

        # 5️⃣ Get Answer
        response = qa.run(final_query)
        print("🧠 AI Response:\n", response)

        return jsonify({"message": response})

    return jsonify({"message": "⚠️ कृपया पहले जन्म विवरण देकर कुंडली बनवाएं।"}), 400
