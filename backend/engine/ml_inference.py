"""
ML Inference Engine
HuggingFace Transformers integration
"""

from typing import Optional
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import torch
import asyncio
from concurrent.futures import ThreadPoolExecutor
import structlog

from utils.types import MLResult
from config import settings

logger = structlog.get_logger()

# Thread pool for blocking ML inference
_executor = ThreadPoolExecutor(max_workers=4)


class MLInferenceEngine:
    """ML model inference using HuggingFace Transformers."""
    
    def __init__(self):
        self.model_cache = {}  # Cache loaded models
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"ML inference initialized on device: {self.device}")
    
    def predict(
        self,
        text: str,
        model_name: str,
        threshold: float = 0.75
    ) -> MLResult:
        """
        Run inference on text.
        
        Args:
            text: Input text to classify
            model_name: HuggingFace model name (e.g., "safe-mcp/T1102-detector")
            threshold: Confidence threshold for triggering (0.0-1.0)
        
        Returns:
            MLResult with prediction and confidence
        """
        try:
            # Load model (cached)
            model_pipeline = self._load_model(model_name)
            if not model_pipeline:
                return MLResult(
                    triggered=False,
                    confidence=0.0,
                    model_name=model_name,
                    prediction="model_not_found"
                )
            
            # Run inference
            result = model_pipeline(text, truncation=True, max_length=512)
            
            # Parse result (format: [{'label': 'LABEL_1', 'score': 0.95}])
            if not result or len(result) == 0:
                return MLResult(triggered=False, confidence=0.0, model_name=model_name)
            
            prediction = result[0]
            label = prediction.get('label', '')
            score = prediction.get('score', 0.0)
            
            # Determine if malicious (LABEL_1 typically = malicious in binary classification)
            is_malicious = (label in ['LABEL_1', '1', 'malicious'])
            
            # If benign but high confidence, invert the score
            if not is_malicious:
                score = 1.0 - score
                is_malicious = score >= threshold
            
            return MLResult(
                triggered=is_malicious and score >= threshold,
                confidence=score,
                model_name=model_name,
                prediction=label
            )
            
        except Exception as e:
            logger.error(f"ML inference failed: {model_name}", error=str(e))
            return MLResult(
                triggered=False,
                confidence=0.0,
                model_name=model_name,
                prediction=f"error: {str(e)}"
            )
    
    def _load_model(self, model_name: str):
        """Load model from HuggingFace (cached)."""
        if model_name in self.model_cache:
            return self.model_cache[model_name]
        
        try:
            logger.info(f"Loading ML model: {model_name}")
            
            # Create pipeline for text classification
            classifier = pipeline(
                "text-classification",
                model=model_name,
                device=0 if self.device == "cuda" else -1,
                cache_dir=settings.ML_MODELS_CACHE_DIR
            )
            
            self.model_cache[model_name] = classifier
            logger.info(f"Model loaded successfully: {model_name}")
            
            return classifier
            
        except Exception as e:
            logger.error(f"Failed to load model: {model_name}", error=str(e))
            return None
    
    async def predict_async(
        self,
        text: str,
        model_name: str,
        threshold: float = 0.75
    ) -> MLResult:
        """
        Async wrapper for predict() - runs in thread pool to avoid blocking.
        
        Args:
            text: Input text to classify
            model_name: HuggingFace model name
            threshold: Confidence threshold
        
        Returns:
            MLResult with prediction
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            self.predict,
            text,
            model_name,
            threshold
        )
    
    def clear_cache(self):
        """Clear model cache (frees memory)."""
        self.model_cache.clear()
        logger.info("ML model cache cleared")


# Global instance
_ml_engine = None


def get_ml_engine() -> MLInferenceEngine:
    """Get global ML inference engine instance."""
    global _ml_engine
    if _ml_engine is None:
        _ml_engine = MLInferenceEngine()
    return _ml_engine

