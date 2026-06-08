"""
CropMD – AI Chatbot Route (RAG + Gemini/OpenAI)
POST /api/chatbot/chat
GET  /api/chatbot/history
DELETE /api/chatbot/history
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

logger = logging.getLogger(__name__)
chatbot_bp = Blueprint("chatbot", __name__)

CONVERSATIONS_COLLECTION = "conversations"

# ── System Prompt with Agricultural RAG Context ───────────────────────────────

SYSTEM_PROMPT = """You are CropMD, an expert agricultural AI assistant specializing in:
- Crop disease diagnosis and treatment
- Pesticide and fertilizer recommendations
- Organic farming alternatives
- Crop management and irrigation advice
- Weather-based disease risk assessment
- Soil health and nutrition

Guidelines:
- Provide specific, actionable advice with dosage and timing where applicable
- Always mention organic alternatives alongside chemical treatments
- Note safety precautions for pesticide use
- Recommend professional consultation for severe or uncertain cases
- Be concise but comprehensive
- Use metric units (g/L, kg/ha) by default

Knowledge base: PlantVillage dataset covering 38 disease classes across tomato, potato,
corn, pepper, apple, grape, strawberry, and other crops.
"""

KNOWLEDGE_CHUNKS = [
    "Tomato Early Blight (Alternaria solani): Use Chlorothalonil 2g/L every 7-10 days. "
    "Rotate with Mancozeb. Drip irrigation, 3-year rotation.",

    "Potato Late Blight (Phytophthora infestans): Most destructive potato disease. "
    "Metalaxyl-M 2.5g/L every 7 days. Monitor Smith Period weather. "
    "Use resistant varieties like Sarpo Mira.",

    "Corn Common Rust (Puccinia sorghi): Apply Propiconazole 1mL/L at VT/R1 stage. "
    "Plant RB gene resistant hybrids for prevention.",

    "General Disease Prevention: Crop rotation every 3 years, drip irrigation, "
    "certified disease-free seed, balanced fertilization (adequate K and Ca), "
    "regular scouting twice weekly.",

    "Organic alternatives: Copper-based bactericides/fungicides (OMRI-listed), "
    "Trichoderma biocontrol, neem oil for pest management, "
    "compost tea for general disease suppression.",

    "Irrigation best practices: Drip irrigation reduces foliar diseases by 60-80%. "
    "Water early morning. Avoid overhead irrigation during disease-favorable conditions. "
    "Maintain 60-80% field capacity.",

    "Fertilizer and immunity: Potassium (K) at adequate levels reduces disease susceptibility. "
    "Calcium strengthens cell walls. Silicon foliar sprays reduce fungal penetration. "
    "Avoid excess nitrogen which promotes soft, disease-susceptible tissue.",
]


# ── Chat Endpoint ─────────────────────────────────────────────────────────────

@chatbot_bp.post("/chat")
@jwt_required()
def chat():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")
    scan_context = data.get("scan_context")  # Optional: attach scan result for context

    if not message:
        return jsonify({"error": "Message is required"}), 400
    if len(message) > 2000:
        return jsonify({"error": "Message too long (max 2000 chars)"}), 400

    db = current_app.db

    # Load or create conversation
    history = []
    if conversation_id:
        conv = db[CONVERSATIONS_COLLECTION].find_one({
            "_id": ObjectId(conversation_id),
            "user_id": ObjectId(user_id),
        })
        if conv:
            history = conv.get("messages", [])

    # Build RAG context
    rag_context = _retrieve_context(message)

    # Build AI response
    try:
        reply = _call_llm(message, history, rag_context, scan_context)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        reply = _fallback_response(message)

    # Persist conversation
    new_messages = history + [
        {"role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()},
        {"role": "assistant", "content": reply, "timestamp": datetime.utcnow().isoformat()},
    ]
    # Keep last 20 exchanges (40 messages)
    new_messages = new_messages[-40:]

    if conversation_id:
        db[CONVERSATIONS_COLLECTION].update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"messages": new_messages, "updated_at": datetime.utcnow()}},
        )
    else:
        result = db[CONVERSATIONS_COLLECTION].insert_one({
            "user_id": ObjectId(user_id),
            "messages": new_messages,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        conversation_id = str(result.inserted_id)

    return jsonify({
        "reply": reply,
        "conversation_id": str(conversation_id),
    })


@chatbot_bp.get("/history")
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    db = current_app.db
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    skip = (page - 1) * limit

    convs = list(
        db[CONVERSATIONS_COLLECTION]
        .find({"user_id": ObjectId(user_id)})
        .sort("updated_at", -1)
        .skip(skip)
        .limit(limit)
    )
    result = []
    for c in convs:
        msgs = c.get("messages", [])
        first_user_msg = next((m["content"] for m in msgs if m["role"] == "user"), "")
        result.append({
            "id": str(c["_id"]),
            "preview": first_user_msg[:80] + "…" if len(first_user_msg) > 80 else first_user_msg,
            "message_count": len(msgs),
            "updated_at": c["updated_at"].isoformat(),
        })
    return jsonify({"conversations": result})


@chatbot_bp.delete("/history/<conv_id>")
@jwt_required()
def delete_conversation(conv_id: str):
    user_id = get_jwt_identity()
    db = current_app.db
    db[CONVERSATIONS_COLLECTION].delete_one({
        "_id": ObjectId(conv_id),
        "user_id": ObjectId(user_id),
    })
    return jsonify({"message": "Conversation deleted"})


# ── LLM Integration ───────────────────────────────────────────────────────────

def _retrieve_context(query: str) -> str:
    """Simple keyword-based RAG over knowledge chunks."""
    query_lower = query.lower()
    relevant = [
        chunk for chunk in KNOWLEDGE_CHUNKS
        if any(word in chunk.lower() for word in query_lower.split() if len(word) > 3)
    ]
    if not relevant:
        relevant = KNOWLEDGE_CHUNKS[:3]
    return "\n\n".join(relevant[:3])


def _call_llm(
    message: str,
    history: list,
    rag_context: str,
    scan_context: dict = None,
) -> str:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    context_block = f"\n\n[Agricultural Knowledge Base]\n{rag_context}"
    if scan_context:
        context_block += (
            f"\n\n[Recent Scan Context]\n"
            f"Crop: {scan_context.get('crop_name')}\n"
            f"Disease: {scan_context.get('disease_name')}\n"
            f"Confidence: {scan_context.get('confidence_pct')}%\n"
            f"Severity: {scan_context.get('severity')}"
        )

    if gemini_key:
        return _call_gemini(message, history, SYSTEM_PROMPT + context_block, gemini_key)
    elif openai_key:
        return _call_openai(message, history, SYSTEM_PROMPT + context_block, openai_key)
    else:
        return _fallback_response(message)


def _call_gemini(message: str, history: list, system: str, api_key: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system,
    )
    # Build history for Gemini
    gemini_history = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
        for m in history[-10:]
    ]
    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(message)
    return response.text


def _call_openai(message: str, history: list, system: str, api_key: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    messages = [{"role": "system", "content": system}]
    for m in history[-10:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=800,
        temperature=0.3,
    )
    return response.choices[0].message.content


def _fallback_response(message: str) -> str:
    """Rule-based fallback when no API key is configured."""
    m = message.lower()
    if any(w in m for w in ["blight", "rust", "spot", "mold", "rot"]):
        return (
            "For fungal and bacterial diseases, the first step is accurate identification. "
            "Upload a leaf image using the Scanner for an AI-powered diagnosis. "
            "General treatments include copper-based fungicides (2–3 g/L) every 7–10 days. "
            "Always use drip irrigation and practice 3-year crop rotation to reduce disease pressure."
        )
    elif any(w in m for w in ["fertilizer", "nutrient", "nitrogen", "potassium"]):
        return (
            "Balanced nutrition is key to disease resistance. "
            "Potassium (K) strengthens cell walls and reduces susceptibility. "
            "Avoid excess nitrogen which promotes soft tissue. "
            "Calcium foliar sprays (0.5% CaCl₂) reduce bacterial infections. "
            "Get a soil test to determine exact requirements."
        )
    elif any(w in m for w in ["water", "irrigation", "drip"]):
        return (
            "Drip irrigation is strongly recommended as it reduces foliar disease by 60–80%. "
            "Maintain soil moisture at 60–80% field capacity. "
            "Water early morning so foliage dries before evening. "
            "Avoid overhead irrigation during disease-favorable conditions."
        )
    return (
        "I'm CropMD, your agricultural AI assistant. I can help with crop disease diagnosis, "
        "treatment recommendations, pesticide choices, fertilizer planning, and irrigation advice. "
        "For the best results, upload a leaf image using the Scanner feature. "
        "Configure GEMINI_API_KEY or OPENAI_API_KEY for full AI chat capability."
    )
