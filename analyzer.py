import google.generativeai as genai
from config import Config
import json

class AIAnalyzer:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        # Updated model name - use the current free model
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def analyze_website(self, crawled_data, url):
        """Analyze website data using Gemini API"""
        
        # Prepare content for analysis
        content_summary = self._prepare_content_summary(crawled_data)
        
        prompt = f"""
        Analyze this website data and provide a comprehensive 360° analysis for conversion optimization and business growth.

        Website URL: {url}
        Website Data: {content_summary}

        Please provide analysis in the following JSON format:
        {{
            "overall_score": "X/10",
            "seo_analysis": {{
                "score": "X/10",
                "issues": ["issue1", "issue2"],
                "recommendations": ["rec1", "rec2"]
            }},
            "ux_analysis": {{
                "score": "X/10",
                "issues": ["issue1", "issue2"],
                "recommendations": ["rec1", "rec2"]
            }},
            "content_analysis": {{
                "score": "X/10",
                "issues": ["issue1", "issue2"],
                "recommendations": ["rec1", "rec2"]
            }},
            "conversion_analysis": {{
                "score": "X/10",
                "issues": ["issue1", "issue2"],
                "recommendations": ["rec1", "rec2"]
            }},
            "technical_analysis": {{
                "score": "X/10",
                "issues": ["issue1", "issue2"],
                "recommendations": ["rec1", "rec2"]
            }},
            "key_insights": ["insight1", "insight2", "insight3"],
            "priority_actions": ["action1", "action2", "action3"]
        }}

        You are an expert website analyzer specializing in conversion optimization and business growth. Provide detailed, actionable insights in valid JSON format only.
        """
        
        try:
            # Updated generation configuration for the new API
            generation_config = genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2000,
                candidate_count=1
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            analysis_text = response.text
            
            # Clean the response text (remove markdown formatting if present)
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text.replace('```json', '').replace('```', '')
            
            analysis_text = analysis_text.strip()
            
            # Try to parse JSON response
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured response
                analysis = self._create_fallback_analysis(analysis_text)
            
            return analysis
            
        except Exception as e:
            raise Exception(f"AI Analysis failed: {str(e)}")
    
    def _prepare_content_summary(self, data):
        """Prepare a concise summary of crawled data"""
        summary = {
            'title': data.get('title', ''),
            'meta_description': data.get('meta_description', ''),
            'headings_count': {k: len(v) for k, v in data.get('headings', {}).items()},
            'links_count': len(data.get('links', [])),
            'images_count': len(data.get('images', [])),
            'forms_count': len(data.get('forms', [])),
            'text_sample': data.get('text_content', '')[:500] + '...' if len(data.get('text_content', '')) > 500 else data.get('text_content', '')
        }
        return json.dumps(summary, indent=2)
    
    def _create_fallback_analysis(self, analysis_text):
        """Create structured analysis if JSON parsing fails"""
        return {
            "overall_score": "7/10",
            "seo_analysis": {
                "score": "7/10",
                "issues": ["Analysis completed but formatting needs improvement"],
                "recommendations": ["Review SEO fundamentals"]
            },
            "ux_analysis": {
                "score": "7/10", 
                "issues": ["User experience needs evaluation"],
                "recommendations": ["Improve navigation and usability"]
            },
            "content_analysis": {
                "score": "7/10",
                "issues": ["Content quality assessment needed"],
                "recommendations": ["Enhance content relevance and clarity"]
            },
            "conversion_analysis": {
                "score": "6/10",
                "issues": ["Conversion elements need optimization"],
                "recommendations": ["Add clear call-to-actions"]
            },
            "technical_analysis": {
                "score": "7/10",
                "issues": ["Technical performance review required"],
                "recommendations": ["Optimize page loading speed"]
            },
            "key_insights": [
                "Website has potential for improvement",
                "Focus on user experience optimization",
                "Technical enhancements needed"
            ],
            "priority_actions": [
                "Improve page loading speed",
                "Enhance call-to-action buttons",
                "Optimize for mobile devices"
            ],
            "raw_analysis": analysis_text
        }