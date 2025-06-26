import google.generativeai as genai
from config import Config
from vector_store import split_text_to_chunks, get_relevant_chunks
import json

class AIAnalyzer:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)

    def analyze_website(self, crawled_data, url):
        """Analyze website using Gemini + RAG-style chunk injection"""

        raw_text = crawled_data.get('text_content', '')
        if not raw_text:
            raise Exception("No content found for analysis.")

        # Step 1: Split website text into smaller chunks
        documents = split_text_to_chunks(raw_text)

        # Step 2: Select relevant chunks based on a fixed query
        prompt_query = "seo ux content technical conversion"
        relevant_chunks = get_relevant_chunks(documents, prompt_query)

        # Debug: Log chunks for verification
        print("🧠 RAG Context Chunks Selected:")
        for i, chunk in enumerate(relevant_chunks):
            print(f"\n--- Chunk {i+1} ---\n{chunk[:500]}...")  # Truncate for readability

        # Step 3: Construct the prompt for Gemini
        combined_context = "\n\n---\n\n".join(relevant_chunks)
        prompt = f"""
You are a website analysis expert. Based on the following extracted content chunks from the website at {url}, give a 360° analysis focused on conversion, UX, SEO, content, and technical factors.

Website URL: {url}

Website Extracted Content:
{combined_context}

Provide output strictly in this JSON format:
{{
  "overall_score": "X/10",
  "seo_analysis": {{
    "score": "X/10",
    "issues": ["..."],
    "recommendations": ["..."]
  }},
  "ux_analysis": {{
    "score": "X/10",
    "issues": ["..."],
    "recommendations": ["..."]
  }},
  "content_analysis": {{
    "score": "X/10",
    "issues": ["..."],
    "recommendations": ["..."]
  }},
  "conversion_analysis": {{
    "score": "X/10",
    "issues": ["..."],
    "recommendations": ["..."]
  }},
  "technical_analysis": {{
    "score": "X/10",
    "issues": ["..."],
    "recommendations": ["..."]
  }},
  "key_insights": ["..."],
  "priority_actions": ["..."]
}}

Only return valid JSON — no extra commentary or formatting.
"""

        try:
            generation_config = genai.types.GenerationConfig(
                temperature=Config.GEMINI_TEMPERATURE,
                max_output_tokens=Config.GEMINI_MAX_TOKENS,
                candidate_count=1
            )

            response = self.model.generate_content(prompt, generation_config=generation_config)
            analysis_text = response.text.strip()

            # Clean up Markdown format if returned
            if analysis_text.startswith("```json"):
                analysis_text = analysis_text.replace("```json", "").replace("```", "").strip()

            # Try parsing to JSON
            return json.loads(analysis_text)

        except json.JSONDecodeError:
            raise Exception("Gemini responded with invalid JSON.")
        except Exception as e:
            raise Exception(f"Gemini RAG analysis failed: {str(e)}")
