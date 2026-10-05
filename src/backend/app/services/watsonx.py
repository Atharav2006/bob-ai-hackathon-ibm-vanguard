import os
import json
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

def get_watsonx_model():
    api_key = os.getenv("WATSONX_API_KEY")
    project_id = os.getenv("WATSONX_PROJECT_ID")
    url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    
    if not api_key or not project_id or api_key == "your_watsonx_api_key_here":
        return None

    credentials = {
        "url": url,
        "apikey": api_key
    }
    
    parameters = {
        GenParams.DECODING_METHOD: "greedy",
        GenParams.MAX_NEW_TOKENS: 200,
        GenParams.MIN_NEW_TOKENS: 1,
        GenParams.TEMPERATURE: 0.0,
        GenParams.REPETITION_PENALTY: 1.0
    }
    
    # Using Granite 13b instruction model for extraction
    model_id = "ibm/granite-13b-instruct-v2"
    
    model = Model(
        model_id=model_id,
        params=parameters,
        credentials=credentials,
        project_id=project_id
    )
    return model

def extract_needs_from_report(raw_text: str):
    """
    Extracts structured data from a raw disaster report using IBM Watsonx Granite.
    """
    model = get_watsonx_model()
    
    prompt = f"""You are a disaster response extraction assistant.
Extract the following information from the field report into a strict JSON object.
Do not include any explanation or markdown formatting outside the JSON.

Fields to extract:
- category: One of ["rescue", "medical", "supply"]
- amount: Numeric value (e.g., 5). If unknown, use null.
- unit: The unit of the amount (e.g., "kits", "people", "litres").
- urgency: An integer from 1 to 5 (5 being most urgent).
- original_language: The ISO language code of the raw text (e.g., "es", "en", "fr").
- english_translation: Translate the raw text into English perfectly.
- sentiment: The emotional state of the sender (e.g., "Panic", "Calm", "Urgent", "Desperate").

Field Report:
"{raw_text}"

JSON Output:
"""
    
    if model is None:
        # Fallback for local dev without credentials
        return {
            "category": "rescue",
            "amount": 3,
            "unit": "people",
            "urgency": 5,
            "original_language": "es",
            "english_translation": "HELP! The bridge collapsed on Main Street. We have 3 injured people, we need a medical team immediately. It looks really bad!",
            "sentiment": "Panic / Desperate",
            "note": "Mocked Watsonx Multi-lingual Translation"
        }
    
    try:
        response = model.generate_text(prompt=prompt)
        # Clean the response string in case the LLM wrapped it in markdown
        clean_json_str = response.strip().strip("```json").strip("```").strip()
        data = json.loads(clean_json_str)
        return data
    except Exception as e:
        print(f"Watsonx extraction failed: {e}")
        return None
