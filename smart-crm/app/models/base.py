"""
Base model with Supabase client
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

    if not url or not key:
        raise ValueError("Supabase URL and Key must be set in environment variables")

    return create_client(url, key)


# Singleton client
_supabase_client = None


def get_db() -> Client:
    """Get singleton Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client
