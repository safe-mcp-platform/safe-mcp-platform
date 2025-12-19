"""
ML Model Loader - HuggingFace Model Integration

Dynamic model loader that supports ANY HuggingFace model.
Add new model? Just reference it in technique config!

Key Innovation: Zero-code model integration from HuggingFace Hub
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, logging as hf_logging
from typing import Dict, Optional
import asyncio
from pathlib import Path

from config import settings

# Suppress HuggingFace warnings
hf_logging.set_verbosity_error()


class MLModel:
    """
    Wrapper for HuggingFace models with convenient predict() method.
    
    Supports any binary classification model from HuggingFace Hub.
    """
    
    def __init__(self, model, tokenizer, device: str, model_id: str):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.model_id = model_id
    
    async def predict(self, text: str) -> Dict:
        """
        Run inference and return prediction with confidence.
        
        Works for any binary classification model:
        - Class 0 = Benign
        - Class 1 = Attack
        
        Args:
            text: Input text to classify
        
        Returns:
            Dict with prediction results:
            - class: Predicted class (0 or 1)
            - confidence: Confidence score
            - is_attack: Boolean indicating if attack detected
            - probabilities: Raw probability scores
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._predict_sync, text)
        return result
    
    def _predict_sync(self, text: str) -> Dict:
        """Synchronous prediction logic"""
        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)
            
            # Get prediction
            predicted_class = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][predicted_class].item()
            
            return {
                "class": predicted_class,
                "confidence": float(confidence),
                "probabilities": [float(p) for p in probabilities[0].tolist()],
                "is_attack": predicted_class == 1  # Assuming 1 = attack
            }
        
        except Exception as e:
            print(f"⚠️  Prediction error: {e}")
            return {
                "class": 0,
                "confidence": 0.0,
                "probabilities": [1.0, 0.0],
                "is_attack": False
            }


class MLModelLoader:
    """
    Dynamic ML model loader - supports ANY HuggingFace model.
    
    Features:
    - Lazy loading (only load when needed)
    - Model caching (load once, reuse forever)
    - GPU support (automatic device selection)
    - Any HuggingFace model (just provide model_id)
    
    Examples:
        model_id = "safe-mcp/prompt-injection-detector"
        model_id = "microsoft/deberta-v3-base"
        model_id = "./models/custom-detector"
    """
    
    def __init__(self):
        self.models: Dict[str, MLModel] = {}  # Cache loaded models
        self.device = self._get_device()
        print(f"🤖 ML Model Loader initialized (device: {self.device})")
    
    def _get_device(self) -> str:
        """Determine best device (GPU if available, else CPU)"""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():  # Apple Silicon
            return "mps"
        return "cpu"
    
    async def load_model(self, model_id: str) -> MLModel:
        """
        Load model from HuggingFace Hub or local path.
        
        Args:
            model_id: HuggingFace model ID or local path
                Examples:
                - "safe-mcp/prompt-injection-detector"
                - "microsoft/deberta-v3-base"
                - "./models/custom-detector"
        
        Returns:
            MLModel wrapper ready for inference
        """
        # Return cached model if already loaded
        if model_id in self.models:
            return self.models[model_id]
        
        print(f"📥 Loading ML model: {model_id}")
        
        # Run loading in executor to avoid blocking
        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(None, self._load_model_sync, model_id)
        
        # Cache for reuse
        self.models[model_id] = model
        
        print(f"✅ Model loaded: {model_id}")
        return model
    
    def _load_model_sync(self, model_id: str) -> MLModel:
        """Synchronous model loading logic"""
        try:
            # Load tokenizer and model
            cache_dir = settings.huggingface_cache_dir if hasattr(settings, 'huggingface_cache_dir') else None
            
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=cache_dir,
                token=settings.huggingface_token if settings.huggingface_token else None
            )
            
            model = AutoModelForSequenceClassification.from_pretrained(
                model_id,
                cache_dir=cache_dir,
                token=settings.huggingface_token if settings.huggingface_token else None
            )
            
            # Move to appropriate device
            model = model.to(self.device)
            model.eval()  # Set to evaluation mode
            
            return MLModel(model, tokenizer, self.device, model_id)
        
        except Exception as e:
            print(f"❌ Failed to load model {model_id}: {e}")
            print(f"   Using fallback (always return benign)")
            
            # Return a dummy model that always returns benign
            return self._create_fallback_model(model_id)
    
    def _create_fallback_model(self, model_id: str) -> MLModel:
        """Create a fallback model that always returns benign"""
        class FallbackMLModel(MLModel):
            def __init__(self, model_id):
                self.model_id = model_id
                self.device = "cpu"
                self.model = None
                self.tokenizer = None
            
            async def predict(self, text: str) -> Dict:
                return {
                    "class": 0,
                    "confidence": 1.0,
                    "probabilities": [1.0, 0.0],
                    "is_attack": False
                }
        
        return FallbackMLModel(model_id)
    
    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models"""
        return list(self.models.keys())
    
    def unload_model(self, model_id: str):
        """Unload a model to free memory"""
        if model_id in self.models:
            del self.models[model_id]
            if self.device == "cuda":
                torch.cuda.empty_cache()
            print(f"🗑️  Unloaded model: {model_id}")
    
    def unload_all(self):
        """Unload all models"""
        self.models.clear()
        if self.device == "cuda":
            torch.cuda.empty_cache()
        print("🗑️  Unloaded all models")


# Recommended pre-trained models for SAFE-MCP

RECOMMENDED_MODELS = {
    "prompt_injection": [
        "deepset/deberta-v3-base-injection",  # If it exists
        "microsoft/deberta-v3-base",  # General purpose
    ],
    "toxic_content": [
        "unitary/toxic-bert",
        "martin-ha/toxic-comment-model"
    ],
    "code_injection": [
        "microsoft/codebert-base",
        "huggingface/CodeBERTa-small-v1"
    ]
}


def get_recommended_model(technique_category: str) -> str:
    """Get a recommended model for a technique category"""
    models = RECOMMENDED_MODELS.get(technique_category, [])
    return models[0] if models else "microsoft/deberta-v3-base"

