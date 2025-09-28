"""
InspectionResult data model for storing product image inspection outcomes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
import json


@dataclass
class InspectionResult:
    """
    Represents the result of a product image inspection.
    
    Attributes:
        image_url: URL of the inspected image
        result: Inspection result (True for pass, False for fail)
        reason: Explanation for the inspection result
        timestamp: When the inspection was performed
        processing_time: Time taken for inspection in seconds
        raw_response: Raw response from the AI model
        model_id: ID of the AI model used for inspection
        prompt_version: Version of the prompt used for inspection
        inspection_stage: Stage information for multi-stage inspections
        stage_details: Detailed information about each inspection stage
    """
    image_url: str
    result: bool
    reason: str
    timestamp: datetime
    processing_time: float
    raw_response: str
    model_id: str = ""
    prompt_version: str = ""
    inspection_stage: str = "single_stage"
    stage_details: Dict[str, Any] = None
    
    def __post_init__(self):
        """Validate inspection result data after initialization."""
        # Initialize stage_details if None
        if self.stage_details is None:
            self.stage_details = {}
        self._validate_data()
    
    def _validate_data(self):
        """Validate inspection result data."""
        if not isinstance(self.image_url, str) or not self.image_url.strip():
            raise ValueError("image_url must be a non-empty string")
        
        if not isinstance(self.result, bool):
            raise ValueError("result must be a boolean")
        
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        
        if not isinstance(self.timestamp, datetime):
            raise ValueError("timestamp must be a datetime object")
        
        if not isinstance(self.processing_time, (int, float)) or self.processing_time < 0:
            raise ValueError("processing_time must be a non-negative number")
        
        if not isinstance(self.raw_response, str):
            raise ValueError("raw_response must be a string")
    
    def is_passed(self) -> bool:
        """Check if inspection passed."""
        return self.result
    
    def is_failed(self) -> bool:
        """Check if inspection failed."""
        return not self.result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert inspection result to dictionary."""
        return {
            'image_url': self.image_url,
            'result': self.result,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'raw_response': self.raw_response
        }
    
    def to_json(self) -> str:
        """Convert inspection result to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InspectionResult':
        """Create InspectionResult from dictionary."""
        # Convert timestamp from ISO format if it's a string
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'InspectionResult':
        """Create InspectionResult from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the inspection result."""
        return {
            'image_url': self.image_url,
            'result': self.result,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'passed': self.is_passed()
        }