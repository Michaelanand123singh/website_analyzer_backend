import os
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from crawler import WebCrawler
from analyzer import AIAnalyzer
from database import Database
from config import Config
from utils import is_valid_url

app = Flask(__name__)
app.config.from_object(Config)

# ✅ CORS setup for specific domains
CORS(app, supports_credentials=True, origins=[
    "http://localhost:3002",
    "https://website-analyzer-frontend-phi.vercel.app",
    "https://www.nothingbefore.com",
    "http://localhost:3000/"
])

# ✅ Handle OPTIONS (preflight) requests with proper headers
@app.before_request
def handle_options_requests():
    if request.method == 'OPTIONS':
        response = app.make_response('')
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = request.headers.get(
            'Access-Control-Request-Headers', '*')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

# Initialize components
crawler = WebCrawler()
analyzer = AIAnalyzer()
db = Database()

# ✅ Optional root route for Render health
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Welcome to the AI Website Analyzer API. Visit /api/health for health check.'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'AI Website Analyzer API is running with Gemini'})

@app.route('/api/analyze', methods=['POST'])
def analyze_website():
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'error': 'URL is required'}), 400
        if not is_valid_url(url):
            return jsonify({'error': 'Invalid URL format'}), 400

        # Step 1: Crawl website
        print(f"Crawling website: {url}")
        crawled_data = crawler.crawl_website(url)
        if not crawled_data:
            return jsonify({'error': 'Failed to crawl website. Please check the URL and try again.'}), 400

        # Step 2: Analyze with Gemini
        print("Analyzing with Gemini AI...")
        analysis = analyzer.analyze_website(crawled_data, url)
        if not analysis:
            return jsonify({'error': 'AI analysis failed. Please try again.'}), 500

        # Step 3: Save to database
        analysis_id = db.save_analysis(url, {
            'crawled_data': crawled_data,
            'analysis': analysis
        })

        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'url': url,
            'analysis': analysis,
            'timestamp': crawled_data.get('timestamp'),
            'ai_provider': 'gemini'
        })

    except Exception as e:
        error_msg = str(e)
        print(f"Error analyzing website: {error_msg}")
        print(traceback.format_exc())

        if "API_KEY" in error_msg.upper():
            return jsonify({'error': 'Gemini API key is missing or invalid. Please check your configuration.'}), 500
        elif "QUOTA" in error_msg.upper() or "RATE_LIMIT" in error_msg.upper():
            return jsonify({'error': 'API quota exceeded or rate limit reached. Please try again later.'}), 429
        elif "NETWORK" in error_msg.upper() or "CONNECTION" in error_msg.upper():
            return jsonify({'error': 'Network connection error. Please check your internet connection.'}), 503
        else:
            return jsonify({'error': f'Analysis failed: {error_msg}'}), 500

@app.route('/api/analysis/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    try:
        result = db.get_analysis(analysis_id)
        if not result:
            return jsonify({'error': 'Analysis not found'}), 404
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print(f"Error retrieving analysis: {str(e)}")
        return jsonify({'error': 'Failed to retrieve analysis'}), 500

@app.route('/api/recent', methods=['GET'])
def get_recent_analyses():
    try:
        limit = request.args.get('limit', 10, type=int)
        recent = db.get_recent_analyses(limit=limit)
        return jsonify({'success': True, 'count': len(recent), 'data': recent})
    except Exception as e:
        print(f"Error retrieving recent analyses: {str(e)}")
        return jsonify({'error': 'Failed to retrieve recent analyses'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = db.get_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        print(f"Error retrieving stats: {str(e)}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ✅ Start the Flask app with proper port binding for Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 Starting AI Website Analyzer with Gemini...")
    print("📋 Available endpoints:")
    print("   • GET  /api/health - Health check")
    print("   • POST /api/analyze - Analyze website")
    print("   • GET  /api/analysis/<id> - Get specific analysis")
    print("   • GET  /api/recent - Get recent analyses")
    print("   • GET  /api/stats - Get analysis statistics")
    print("⚠️  Make sure to set GEMINI_API_KEY in your .env file")
    print(f"🌐 Server starting on http://0.0.0.0:{port}")

    app.run(debug=Config.DEBUG, host='0.0.0.0', port=port)
