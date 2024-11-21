# src/chatbot.py

import os
import gradio as gr
from guardrails import Guard
from guardrails.errors import ValidationError
from dotenv import load_dotenv
from utils import load_qa_pairs, detect_language, translate_text
from rag import RAG
from web_search import WebSearch
import anthropic

# .env dosyasını yükleyin
load_dotenv()

# Anthropic API anahtarınızı alın
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
COMPANY_WEBSITE_URL = os.getenv("COMPANY_WEBSITE_URL")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment değişkeninde bulunamadı.")

if not COMPANY_WEBSITE_URL:
    raise ValueError("COMPANY_WEBSITE_URL environment değişkeninde bulunamadı.")

# QA çiftlerini yükleyin
qa_pairs = load_qa_pairs("data/qa_pairs.xlsx")

# Guardrails'ı başlatın
guard = Guard(config="src/guardrails_config.yaml")

# Anthropics API istemcisini başlatın
client = anthropic.Client(api_key=ANTHROPIC_API_KEY)

# RAG'ı başlatın
rag = RAG()

# WebSearch'i başlatın
web_search = WebSearch(COMPANY_WEBSITE_URL)

# Sistem mesajı
base_message = {
    "role": "system",
    "content": """You are a helpful mentor assistant.

Use the provided documents to answer the user's question.

${document}
"""
}

# Contact Information
contact_info = """
Daha detaylı mentorluk desteği için lütfen bizimle iletişime geçin:
- Email: info@techproeducation.com
- Phone: +1 234 567 8900
- Website: https://www.techproeducation.com
"""

def history_to_messages(history, document):
    messages = [base_message.copy()]
    messages[0]['content'] = messages[0]['content'].replace("${document}", document)
    for message in history:
        messages.append({"role": "user", "content": message[0]})
        messages.append({"role": "assistant", "content": message[1]})
    return messages

def get_response_from_anthropic(messages):
    # Anthropics API'ye uygun formatta istek gönderin
    prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages]) + "\nassistant:"

    try:
        response = client.completion(
            prompt=prompt,
            model="claude-v1",  # Kullanmak istediğiniz model
            max_tokens_to_sample=150,
            temperature=0.7,
            stop_sequences=["\nuser:", "\nassistant:"]
        )
        return response.completion.strip()
    except Exception as e:
        print(f"API Hatası: {e}")
        return "Üzgünüm, şu anda yardımcı olamıyorum."

def is_relevant_question(user_input):
    # Mentorlikle ilgili anahtar kelimeler
    relevant_keywords = ['mentor', 'mentorluk', 'eğitim', 'ders', 'öğrenme', 'destek']
    return any(keyword in user_input.lower() for keyword in relevant_keywords)

def chatbot_response(user_input, history):
    language = detect_language(user_input)
    
    # Kullanıcının diline göre çeviri
    if language != 'tr':
        translated_input = translate_text(user_input, 'tr')
    else:
        translated_input = user_input
    
    # Excel'deki sorularla eşleşme
    answer = qa_pairs.get(user_input, None)
    
    # Şirket web sitesinde arama yap
    web_results = web_search.search(translated_input)
    web_document = "\n".join(web_results) if web_results else ""
    
    if answer:
        response = answer
    else:
        # RAG kullanarak ilgili belgeleri al
        relevant_docs = rag.get_relevant_documents(translated_input)
        combined_document = "\n".join(relevant_docs) + "\n" + web_document
        
        # Yanıtı Anthropic API'den al
        response = get_response_from_anthropic(history_to_messages(history, combined_document) + [{"role": "user", "content": translated_input}])
    
    # Guardrails ile doğrulama
    try:
        validated_response = guard(response)
    except ValidationError:
        validated_response = "Üzgünüm, bu konuda yardımcı olamam."
    
    # Gelişmiş guardrails kurallarını uygulama
    if not is_relevant_question(user_input):
        validated_response = "Üzgünüm, bu bir mentorluk faaliyeti değildir. Daha fazla bilgi için lütfen bizimle iletişime geçin:\n" + contact_info
    
    # Kullanıcının diline çeviri
    if language != 'tr':
        validated_response = translate_text(validated_response, language)
    
    return validated_response, history + [[user_input, validated_response]]

def log_feedback(question, response, feedback):
    with open("feedback.log", "a", encoding='utf-8') as f:
        f.write(f"{question}\t{response}\t{feedback}\n")

def main():
    with gr.Blocks() as demo:
        # **Üst Kısım: Logo ve Banner**
        with gr.Row():
            gr.Image("images/logo.png", label="Logo", elem_id="logo")
            # Eğer bir banner eklemek isterseniz, aşağıdaki satırı kullanabilirsiniz:
            gr.Image("images/banner.jpg", label="Banner", elem_id="banner")
        
        # **Başlık**
        gr.Markdown("# Mentoring Assistant")
        
        # **Sohbet Arayüzü**
        chatbot = gr.Chatbot()
        msg = gr.Textbox(label="Soru", placeholder="Sorunuzu yazın...")
        clear = gr.Button("Temizle")
        
        # **Geri Bildirim Butonları**
        with gr.Row():
            like_btn = gr.Button("👍 Like")
            dislike_btn = gr.Button("👎 Dislike")
            copy_btn = gr.Button("📋 Kopyala")
        
        # **Fonksiyonlar**
        def respond(message, chat_history):
            response, updated_history = chatbot_response(message, chat_history)
            return response, updated_history
        
        def handle_like(chat_history):
            if chat_history:
                log_feedback(chat_history[-1][0], chat_history[-1][1], "like")
            return chat_history
        
        def handle_dislike(chat_history):
            if chat_history:
                log_feedback(chat_history[-1][0], chat_history[-1][1], "dislike")
            return chat_history
        
        def handle_copy(chat_history):
            if chat_history:
                response = chat_history[-1][1]
                return response
            return ""
        
        # **Olay Bağlantıları**
        msg.submit(respond, [msg, chatbot], [chatbot, chatbot])
        clear.click(lambda: (None, []), None, [chatbot, chatbot], queue=False)
        like_btn.click(handle_like, inputs=chatbot, outputs=chatbot)
        dislike_btn.click(handle_dislike, inputs=chatbot, outputs=chatbot)
        copy_btn.click(handle_copy, inputs=chatbot, outputs=msg)
        
        # **Özel CSS Eklemek (Opsiyonel)**
        gr.HTML("""
        <style>
        logo {
            width: 100px;
            height: auto;
            margin-right: 20px;
        }
        /* Eğer bir banner eklediyseniz, aşağıdaki CSS'i kullanabilirsiniz */
        /* #banner {
            width: 100%;
            height: auto;
        } */
        </style>
        """)
    
    demo.launch()

if __name__ == "__main__":
    main()
