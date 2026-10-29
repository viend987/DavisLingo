import json
import re
import requests

def sanitize_radio_comms(text):
    """
    Sanitizes GTA RP / Police / Emergency radio traffic to eliminate redundant duplicate commands.
    In real radio comms, saying duplicate commands like '10-4 copy Officer' or 'Copy that, 10-4'
    is redundant and wastes airtime. This function guarantees crisp, single-command clarity:
    - '10-4 copy Officer' -> '10-4, Officer'
    - '10-4 copy that, Officer' -> '10-4, Officer'
    - '10-4 copy that' -> '10-4'
    - 'Copy that, 10-4' -> 'Copy that'
    - 'Roger that, 10-4' -> 'Roger that'
    - '10-4 roger Officer' -> '10-4, Officer'
    """
    if not text or not isinstance(text, str):
        return text

    # 1. Deduplicate verbal acknowledgment followed by 10-4:
    # e.g., 'Copy that, 10-4', 'Roger that, 10-4', 'Copy 10-4 Officer' -> keep verbal acknowledgment
    text = re.sub(
        r'\b(copy\s+that|roger\s+that|copy|roger|understood|affirmative)\s*[,.\-/\s]+\s*10-4\b',
        r'\1,',
        text,
        flags=re.IGNORECASE
    )

    # 2. Deduplicate 10-4 followed by verbal acknowledgment:
    # e.g., '10-4 copy Officer', '10-4 copy that', '10-4 roger', '10-4 affirmative' -> keep '10-4,'
    text = re.sub(
        r'\b10-4\s*[,.\-/\s]+\s*(?:copy\s+that|roger\s+that|copy|roger|understood|affirmative)\b',
        '10-4,',
        text,
        flags=re.IGNORECASE
    )

    # 3. Clean up trailing comma before punctuation or end of string
    text = re.sub(r',\s*([.!?:;,]|$)', r'\1', text)

    # 4. Clean up multiple consecutive commas or misplaced punctuation spaces
    text = re.sub(r',\s*,+', ',', text)
    text = re.sub(r'\s+([,.:?!])', r'\1', text)
    text = re.sub(r',([A-Za-z0-9])', r', \1', text)
    return text.strip()

class UnifiedAiService:
    def __init__(self, config_manager):
        self.config = config_manager
        self.timeout = 10

    def sanitize_radio_comms(self, text):
        return sanitize_radio_comms(text)

    def get_provider(self):
        return self.config.get("ai_provider", "groq").lower()

    def translate_outgoing(self, text, style="LSFD / Fire & Medic", tone="Neutral", ignore_words=""):
        clean_text = text.strip()
        if not clean_text:
            return ""

        prompt = f"""You are an elite GTA V Roleplay (FiveM / JGVRP) English Translator for Indonesian players.
Your job is to translate Indonesian player speech, actions, or radio calls into natural, authentic, context-perfect GTA V Roleplay English.

ROLEPLAY PERSONA & STYLE:
- Selected Style: {style}
- Emotion / Tone: {tone}
- Protected Entities (DO NOT translate or modify): {ignore_words}

STYLE GUIDELINES:
- "LSFD / Fire & Medic": Los Santos Fire Department & Paramedic doctrine. Calm under pressure, firm, professional, and empathetic to patients.
  CRITICAL RULE FOR LSFD: NEVER inject or force department radio code numbers (such as Status-2, Status-6, 10-codes) unless the player explicitly typed code numbers in the input. Use natural responder language instead, such as "Copy that", "Roger that", "Understood", "Paramedics on scene", "Stay calm, we're taking care of you", "Affirmative", "Stand by".
- "LSPD / Police & Sheriff": Law enforcement officer (Police / Sheriff / State Trooper). Authoritative, procedural, calm, and assertive yet professional.
  CRITICAL RULE FOR LSPD: Use natural, realistic law enforcement communications: "Copy that", "Roger that", "Understood", "Driver, turn off the engine", "Keep your hands visible", "Affirmative", "Dispatch, unit en route", "Area secure".
- "LA Street Gang": Authentic Los Angeles / Davis hood dialect (AAVE). Gritty, natural, punchy West Coast street slang without being a caricature.
- "Casual Civilian": Everyday natural conversational American English. Relaxed, polite, realistic.
- "Cartel & Latino": Streetwise bilingual Latin American / Mexican cartel roleplay (hermano, jefe, tranquilo, compa). Cool, calculated, respectful or menacing.
- "Mafia Underworld": Articulate, polished, calm, cold, organized crime demeanor ("Let's keep this business between gentlemen").

CRITICAL RULES:
1. GOVERNMENT FACTION (PD/SD/FD) RADIO DISCIPLINE & ZERO REDUNDANCY:
   - In realistic law enforcement & emergency radio communications, repeating the same acknowledgment twice (e.g. "10-4 copy Officer", "10-4 copy that", "Copy that, 10-4", "10-4 roger", "10-4 understood") is redundant, unprofessional, and wastes critical radio airtime.
   - ALWAYS choose ONLY ONE single acknowledgment command:
     * EITHER use the 10-code alone: "10-4." or "10-4, Officer." or "10-4, heading to the location."
     * OR use the verbal acknowledgment alone: "Copy that." or "Roger that." or "Understood, Officer." or "Copy, on my way."
     * NEVER combine "10-4" and "copy" / "roger" / "understood" in the same response!
   - DO NOT invent numerical codes (10-4, Status-2) unless the user's input explicitly contains them or radio context demands it. When in doubt, prefer natural professional terms: "Copy that", "Roger that", "Understood", "Affirmative".
2. PRESERVE CHAT COMMAND PREFIXES:
   If the input starts with a GTA V / FiveM command prefix (e.g. '/me ', '/do ', '/r ', '/d ', '/b ', '/s ', '/w ', '/m ', '/f ', '/looc '):
   Keep that exact command prefix at the very beginning of the translated output.
   - Example: '/me memeriksa denyut nadi korban' -> '/me checks the victim\\'s pulse'
   - Example: '/do apakah terlihat ada pendarahan?' -> '/do does the patient show signs of external bleeding?'
   - Example: '/r siap saya menuju ke lokasi' -> '/r Copy that, heading to the location now.'
   - Example: '/r 10-4 siap pak' -> '/r 10-4, heading to the location.' (or '/r Copy that, Officer.')
   - Example: '/b tunggu bentar lag' -> '/b wait a second, lagging'
3. DIALOGUE & ACTION TRANSLATION:
   Translate the Indonesian speech into punchy, concise, realistic English matching the chosen Persona and Emotion/Tone.
4. STRICT OUTPUT:
   Return ONLY the translated string. Do NOT add quotes, markdown, prefixes, or explanatory notes.

INPUT:
{clean_text}"""

        raw_output = self._call_groq(prompt, is_json=False)
        return sanitize_radio_comms(raw_output)

    def translate_and_reply_incoming(self, ocr_text):
        clean_text = ocr_text.strip()
        if not clean_text:
            return {
                "terjemahan_ocr": "Area kosong atau tidak ada teks terbaca.",
                "status": "idle",
                "opsi_id": ["Diterima.", "Semua aman.", "Ada urusan apa?"],
                "opsi_en": ["Copy that.", "All good out here.", "What's going on?"]
            }

        style = self.config.get("current_style", "LSFD / Fire & Medic")
        tone = self.config.get("emotion_tone", "Neutral")

        prompt = f"""You are an elite GTA V Roleplay (FiveM / JGVRP) AI Assistant for an Indonesian player.
You receive scanned in-game chat text (which might contain minor OCR reading typos from game fonts).

YOUR ROLEPLAY CHARACTER PROFILE:
- Persona / Faction Style: {style}
- Emotion / Tone: {tone}

PERSONA CONTEXT:
- "LSFD / Fire & Medic": You are an LSFD firefighter / paramedic (from JGVRP doctrine ems.viend.my.id). You are firm, professional, calm under high pressure, empathetic to victims, but commanding when controlling emergency perimeters. You know radio traffic (Status-2, Status-4, Status-6 on scene, Status-7e transport, 10-4, 10-20 location, CAT-A/B/C) and clinical/rescue actions (/me, /do, ILS Bag, BLS).
- "LSPD / Police & Sheriff": You are a law enforcement officer. Authoritative, procedural, commanding, assertive yet professional.
- "LA Street Gang": You are a South Central / Davis local. Street-smart, authentic West Coast slang, sharp, loyal to the block.
- "Casual Civilian": Normal citizen of Los Santos. Natural, conversational, polite or relaxed everyday English.
- "Cartel & Latino": Bilingual Latin syndicate roleplay. Respectful, calculating, calm with Spanish loanwords (hermano, jefe, tranquilo).
- "Mafia Underworld": Sophisticated, articulate, respectful on the surface with covert menace.

TASKS:
1. Clean and correct any minor OCR reading typos from the input text.
2. Translate the scanned text into natural, easy-to-understand Indonesian colloquial speech ('terjemahan_ocr').
3. CONTEXT ANALYSIS:
   - Identify who spoke and what is happening (e.g. citizen asking help, officer giving an order, radio dispatch, gang threat, medical status).
4. GENERATE EXACTLY 3 DISTINCT, HIGHLY REALISTIC GTA V ROLEPLAY REPLIES ('opsi_en') AND CLEAR INDONESIAN EXPLANATIONS ('opsi_id'):
   - Option 1 (Direct / Professional / Cooperative): The most direct, standard response that addresses the conversation smoothly.
   - Option 2 (Cautious / Inquisitive / De-escalating): Asks for details, clarifies, or responds with polite hesitation.
   - Option 3 (Assertive / Action-Oriented / Conclusive): A firm stance, tactical command, counter-argument, or roleplay action (/me or decisive statement).
   - CRITICAL REQUIREMENT FOR 'opsi_id': Indonesian players may have limited English proficiency. In 'opsi_id', provide a clear Indonesian translation PLUS a short bracketed tag explaining the intent/vibe so they know exactly what they are picking (e.g. "(Koperatif/Menuruti perintah)", "(Santai/Gak cari ribut)", "(Tegas/Periksa pasien)", "(Radio LSFD 10-4)").
5. RADIO COMM DISCIPLINE & EFFICIENCY:
   - NEVER generate redundant double-acknowledgments like "10-4 copy Officer", "10-4 copy that", "Copy that, 10-4", or "10-4 roger".
   - Pick ONLY ONE: EITHER "10-4, Officer." OR "Copy that, Officer." / "Roger that." - never stack duplicate affirmation commands in one sentence.

OUTPUT FORMAT (STRICT JSON ONLY, DO NOT LEAVE LISTS EMPTY):
{{
  "terjemahan_ocr": "string (terjemahan chat lawan bicara ke bahasa Indonesia santai)",
  "status": "ready",
  "opsi_id": [
    "Terjemahan Opsi 1 dalam Bahasa Indonesia (Penjelasan maksud/vibe)",
    "Terjemahan Opsi 2 dalam Bahasa Indonesia (Penjelasan maksud/vibe)",
    "Terjemahan Opsi 3 dalam Bahasa Indonesia (Penjelasan maksud/vibe)"
  ],
  "opsi_en": [
    "Option 1 in English tailored to chosen Persona & Context",
    "Option 2 in English tailored to chosen Persona & Context",
    "Option 3 in English tailored to chosen Persona & Context"
  ]
}}

SCANNED OCR TEXT:
{clean_text}"""

        try:
            raw = self._call_groq(prompt, is_json=True)
            return self._parse_json_response(raw)
        except Exception as e:
            return {
                "terjemahan_ocr": f"[AI Error] {str(e)}",
                "status": "error",
                "opsi_id": ["Diterima.", "Semua aman.", "Ada urusan apa?"],
                "opsi_en": ["Copy that.", "All good out here.", "What's going on?"]
            }

    def get_safe_fallback_replies(self, text):
        clean = text.strip() if text else "Teks terdeteksi."
        return {
            "terjemahan_ocr": clean,
            "status": "ready",
            "opsi_id": [
                "Diterima, jelas dan terdengar.",
                "Dimengerti, saya segera merespons.",
                "Semua aman di sini, tetap siaga."
            ],
            "opsi_en": [
                "Copy that. Loud and clear.",
                "Understood, on it right now.",
                "All good out here, standing by."
            ]
        }

    def _call_groq(self, prompt, is_json=False, max_tokens=None):
        api_key = self.config.get("groq_api_key", "").strip()
        if not api_key:
            raise RuntimeError("Groq API Key belum terpasang.")

        model = self.config.get("groq_model", "qwen/qwen3.8-27b")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        if max_tokens is None:
            max_tokens = 450 if is_json else 200

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an elite GTA V Roleplay translation engine. Always follow instructions strictly."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": max_tokens
        }

        if is_json:
            payload["response_format"] = {"type": "json_object"}

        res = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        if res.status_code != 200:
            raise RuntimeError(f"Groq API Error ({res.status_code}): {res.text}")

        data = res.json()
        content = data["choices"][0]["message"]["content"].strip()
        if not is_json:
            if content.startswith('"') and content.endswith('"') and len(content) > 1:
                content = content[1:-1]
        return content

    def _parse_json_response(self, raw_str):
        if not raw_str:
            return self.get_safe_fallback_replies("")

        # Clean thinking blocks or markdown fences if present
        clean_str = re.sub(r"<think>.*?</think>", "", str(raw_str), flags=re.DOTALL).strip()
        if clean_str.startswith("```"):
            clean_str = re.sub(r"^```(?:json)?\s*", "", clean_str, flags=re.IGNORECASE)
            clean_str = re.sub(r"\s*```$", "", clean_str).strip()

        parsed = None
        try:
            parsed = json.loads(clean_str)
        except Exception:
            match = re.search(r"\{.*\}", clean_str, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except Exception:
                    pass

        if not parsed or not isinstance(parsed, dict):
            return self.get_safe_fallback_replies(clean_str)

        # Guard: Ensure we ALWAYS have at least 3 viable GTA RP reply options!
        opts_en = [sanitize_radio_comms(str(x).strip()) for x in parsed.get("opsi_en", []) if str(x).strip()]
        opts_id = [str(x).strip() for x in parsed.get("opsi_id", []) if str(x).strip()]

        fallback_pairs = [
            ("Copy that. Loud and clear.", "Diterima, jelas dan terdengar."),
            ("Understood. Give me a second on that.", "Dimengerti. Beri saya waktu sebentar."),
            ("All good out here, standing by.", "Semua aman di sini, tetap siaga.")
        ]

        if len(opts_en) < 3:
            needed = 3 - len(opts_en)
            for idx in range(needed):
                fb_en, fb_id = fallback_pairs[idx % len(fallback_pairs)]
                opts_en.append(sanitize_radio_comms(fb_en))
                opts_id.append(fb_id)

        parsed["opsi_en"] = [sanitize_radio_comms(x) for x in opts_en[:3]]
        parsed["opsi_id"] = opts_id[:3]
        parsed["status"] = "ready"
        return parsed
