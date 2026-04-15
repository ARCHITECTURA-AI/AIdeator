"""Public sharing logic for reports."""

import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Dict, Optional

_STORAGE_PATH = Path("data/shares.json")

def _get_shares() -> Dict[str, dict]:
    if not _STORAGE_PATH.exists():
        return {}
    try:
        return json.loads(_STORAGE_PATH.read_text(encoding="utf-8"))
    except:
        return {}

def _save_shares(shares: Dict[str, dict]):
    _STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORAGE_PATH.write_text(json.dumps(shares, indent=2), encoding="utf-8")

def generate_share_link(idea_id: UUID, expiry_days: int = 7) -> str:
    """Generate a share hash and store it with an expiry date."""
    salt = "NEXUS_SALT_2024"
    hash_obj = hashlib.sha256(f"{idea_id}{salt}{datetime.now()}".encode())
    share_hash = hash_obj.hexdigest()[:16]  # Short hash
    
    expiry = datetime.now(timezone.utc) + timedelta(days=expiry_days)
    
    shares = _get_shares()
    shares[share_hash] = {
        "idea_id": str(idea_id),
        "expiry": expiry.isoformat()
    }
    _save_shares(shares)
    
    return share_hash

def validate_share_hash(share_hash: str) -> Optional[UUID]:
    """Validate hash and return idea_id if still valid."""
    shares = _get_shares()
    share_data = shares.get(share_hash)
    
    if not share_data:
        return None
        
    expiry = datetime.fromisoformat(share_data["expiry"])
    if datetime.now(timezone.utc) > expiry:
        # Clean up expired hash
        del shares[share_hash]
        _save_shares(shares)
        return None
        
    return UUID(share_data["idea_id"])
