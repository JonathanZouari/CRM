"""
Smart CRM Application Entry Point
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'

    print(f"""
    ===========================================================
                        Smart CRM API
    ===========================================================
      Running on: http://localhost:{port}
      Debug mode: {debug}
      API Docs:   http://localhost:{port}/api/health
    ===========================================================
    """)

    app.run(host='0.0.0.0', port=port, debug=debug)
