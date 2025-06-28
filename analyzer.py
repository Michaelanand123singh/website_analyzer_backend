import google.generativeai as genai
from config import Config
from vector_store import split_text_to_chunks, get_relevant_chunks
import json
import re
from urllib.parse import urlparse

class AIAnalyzer:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
    def extract_technical_metrics(self, crawled_data, url):
        """Extract technical metrics from crawled data"""
        metrics = {
            'page_size': len(crawled_data.get('text_content', '')),
            'image_count': len(crawled_data.get('images', [])),
            'link_count': len(crawled_data.get('links', [])),
            'form_count': len(crawled_data.get('forms', [])),
            'heading_structure': self._analyze_heading_structure(crawled_data.get('headings', {})),
            'meta_present': bool(crawled_data.get('meta_description', '')),
            'title_length': len(crawled_data.get('title', '')),
            'is_https': url.startswith('https://'),
            'domain_age_score': self._estimate_domain_credibility(url)
        }
        return metrics

    def _analyze_heading_structure(self, headings):
        """Analyze heading hierarchy"""
        structure_score = 0
        has_h1 = len(headings.get('h1', [])) > 0
        has_proper_hierarchy = True
        
        if has_h1:
            structure_score += 3
        
        # Check if there are multiple H1s (bad practice)
        if len(headings.get('h1', [])) > 1:
            structure_score -= 2
            
        # Check for logical hierarchy
        total_headings = sum(len(h) for h in headings.values())
        if total_headings > 0:
            structure_score += min(2, total_headings // 3)
            
        return max(0, min(5, structure_score))

    def _estimate_domain_credibility(self, url):
        """Simple domain credibility estimation"""
        domain = urlparse(url).netloc
        # Simple heuristics - can be enhanced with actual domain age APIs
        if any(keyword in domain for keyword in ['gov', 'edu', 'org']):
            return 5
        elif len(domain.split('.')) >= 3:  # subdomain
            return 3
        else:
            return 4

    def analyze_website(self, crawled_data, url):
        """Enhanced website analysis with comprehensive parameters"""
        
        raw_text = crawled_data.get('text_content', '')
        if not raw_text:
            raise Exception("No content found for analysis.")

        # Extract technical metrics
        tech_metrics = self.extract_technical_metrics(crawled_data, url)
        
        # RAG-style chunk processing
        documents = split_text_to_chunks(raw_text)
        prompt_queries = [
            "seo keywords meta title description",
            "user experience navigation usability",
            "content quality readability engagement",
            "conversion optimization cta forms",
            "performance speed mobile responsive",
            "security accessibility compliance",
            "social media integration sharing"
        ]
        
        all_relevant_chunks = []
        for query in prompt_queries:
            chunks = get_relevant_chunks(documents, query)
            all_relevant_chunks.extend(chunks[:2])  # Top 2 chunks per category
        
        # Remove duplicates while preserving order
        seen = set()
        unique_chunks = []
        for chunk in all_relevant_chunks:
            if chunk not in seen:
                seen.add(chunk)
                unique_chunks.append(chunk)
        
        combined_context = "\n\n---\n\n".join(unique_chunks[:8])  # Limit to 8 chunks
        
        # Enhanced analysis prompt
        prompt = f"""
You are an expert website analyzer. Analyze the website at {url} across multiple comprehensive parameters.

Website Data:
- URL: {url}
- Title: {crawled_data.get('title', 'N/A')}
- Meta Description: {crawled_data.get('meta_description', 'N/A')}
- Page Size: {tech_metrics['page_size']} characters
- Images: {tech_metrics['image_count']}
- Links: {tech_metrics['link_count']}
- Forms: {tech_metrics['form_count']}
- HTTPS: {tech_metrics['is_https']}
- Heading Structure Score: {tech_metrics['heading_structure']}/5

Content Chunks:
{combined_context}

Provide a comprehensive analysis in this exact JSON format:

{{
  "overall_score": "X/10",
  "category_scores": {{
    "seo": "X/10",
    "user_experience": "X/10", 
    "content_quality": "X/10",
    "conversion_optimization": "X/10",
    "technical_performance": "X/10",
    "security_accessibility": "X/10",
    "mobile_optimization": "X/10",
    "social_integration": "X/10"
  }},
  "detailed_analysis": {{
    "seo": {{
      "title_optimization": "X/10",
      "meta_description": "X/10", 
      "heading_structure": "X/10",
      "keyword_usage": "X/10",
      "url_structure": "X/10",
      "issues": ["..."],
      "recommendations": ["..."]
    }},
    "user_experience": {{
      "navigation_clarity": "X/10",
      "page_layout": "X/10",
      "readability": "X/10", 
      "loading_perception": "X/10",
      "issues": ["..."],
      "recommendations": ["..."]
    }},
    "content_quality": {{
      "relevance": "X/10",
      "depth": "X/10",
      "engagement": "X/10",
      "freshness": "X/10", 
      "issues": ["..."],
      "recommendations": ["..."]
    }},
    "conversion_optimization": {{
      "cta_effectiveness": "X/10",
      "form_optimization": "X/10",
      "trust_signals": "X/10",
      "user_flow": "X/10",
      "issues": ["..."],
      "recommendations": ["..."]
    }},
    "technical_performance": {{
      "page_structure": "X/10",
      "code_quality": "X/10",
      "seo_technical": "X/10",
      "performance_indicators": "X/10",
      "issues": ["..."],
      "recommendations": ["..."]
    }},
    "security_accessibility": {{
      "https_implementation": "X/10",
      "accessibility_basics": "X/10", 
      "privacy_compliance": "X/10",
      "security_indicators": "X/10",
      "issues": ["..."],
      "recommendations": ["..."]
    }},
    "mobile_optimization": {{
      "responsive_design": "X/10",
      "mobile_usability": "X/10",
      "touch_optimization": "X/10",
      "mobile_performance": "X/10",
      "issues": ["..."],
      "recommendations": ["..."]
    }},
    "social_integration": {{
      "social_sharing": "X/10",
      "social_proof": "X/10",
      "social_media_links": "X/10",
      "open_graph": "X/10",
      "issues": ["..."],
      "recommendations": ["..."]
    }}
  }},
  "key_insights": ["..."],
  "priority_actions": ["..."],
  "competitive_advantages": ["..."],
  "risk_factors": ["..."]
}}

Return only valid JSON with no extra text or formatting.
"""

        try:
            generation_config = genai.types.GenerationConfig(
                temperature=Config.GEMINI_TEMPERATURE,
                max_output_tokens=Config.GEMINI_MAX_TOKENS,
                candidate_count=1
            )

            response = self.model.generate_content(prompt, generation_config=generation_config)
            analysis_text = response.text.strip()

            # Clean response
            if analysis_text.startswith("```json"):
                analysis_text = analysis_text.replace("```json", "").replace("```", "").strip()

            analysis_result = json.loads(analysis_text)
            
            # Add technical metrics to response
            analysis_result['technical_metrics'] = tech_metrics
            analysis_result['analysis_metadata'] = {
                'chunks_analyzed': len(unique_chunks),
                'content_length': len(raw_text),
                'analysis_timestamp': self._get_timestamp()
            }
            
            return analysis_result

        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from AI: {str(e)}")
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def generate_summary_report(self, analysis_result):
        """Generate executive summary from detailed analysis"""
        try:
            overall_score = analysis_result.get('overall_score', 'N/A')
            category_scores = analysis_result.get('category_scores', {})
            
            # Find strongest and weakest areas
            scores = {k: float(v.split('/')[0]) for k, v in category_scores.items() if '/' in v}
            strongest_area = max(scores, key=scores.get) if scores else 'N/A'
            weakest_area = min(scores, key=scores.get) if scores else 'N/A'
            
            summary = {
                'overall_score': overall_score,
                'total_parameters_analyzed': 32,  # 8 categories × 4 sub-parameters each
                'strongest_area': strongest_area.replace('_', ' ').title(),
                'weakest_area': weakest_area.replace('_', ' ').title(),
                'key_insights': analysis_result.get('key_insights', [])[:3],
                'priority_actions': analysis_result.get('priority_actions', [])[:3],
                'analysis_completeness': '100%'
            }
            
            return summary
            
        except Exception as e:
            return {'error': f"Summary generation failed: {str(e)}"}