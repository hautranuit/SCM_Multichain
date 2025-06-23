"""
Shipping API Routes
Handles all shipping-related operations for the comprehensive workflow
"""
import time
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from app.services.shipping_service import shipping_service