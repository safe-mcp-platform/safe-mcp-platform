# Contributing to SAFE-MCP-Platform

**Welcome! 🎉** We're building the world's first comprehensive MCP security framework, and we need your help!

## 🎯 Project Vision

SAFE-MCP-Platform aims to operationalize all 81 attack techniques documented in the [SAFE-MCP framework](https://github.com/safe-mcp/safe-mcp). We've built the complete framework architecture and fully implemented the **Top 2 most critical techniques** (covering 80% of real-world attacks). Now we need the community to help cover the remaining 79 techniques.

**Why contribute?**
- 🔒 Secure the emerging MCP ecosystem
- 🏆 Get public recognition (Contributors wall of fame)
- 📚 Learn about AI security & MCP
- 💼 Build your security expertise
- 🤝 Join a growing community

---

## 🚀 Quick Start

### 1. Find a Technique to Implement

Browse [available techniques](https://github.com/safe-mcp-platform/safe-mcp-platform/issues?label=help-wanted) and claim one by commenting on the issue.

### 2. Choose Your Contribution Level

We have **3 levels** of contribution, from beginner to advanced:

| Level | What You Add | Skills Needed | Time | Impact |
|-------|--------------|---------------|------|--------|
| **🟢 Level 1: Patterns** | Regex patterns | Basic regex, JSON | 2-4 hours | Detect known attacks |
| **🟡 Level 2: Rules** | Validation logic | Python, security | 6-10 hours | High-accuracy detection |
| **🔴 Level 3: ML** | Fine-tuned models | ML, PyTorch | 2-4 weeks | Novel attack detection |

**Don't worry!** You can start with Level 1 and upgrade later.

### 3. Use Our Templates

We provide complete templates and reference examples (T1102, T1105) to make it easy.

---

## 🟢 Level 1: Pattern Contributor (EASIEST)

**Perfect for:** Students, beginners, anyone who wants to contribute quickly

**What you'll add:** Regex patterns to detect known attack signatures

### Step-by-Step Guide

#### 1. Fork & Clone

```bash
git fork https://github.com/safe-mcp-platform/safe-mcp-platform
git clone https://github.com/YOUR-USERNAME/safe-mcp-platform
cd safe-mcp-platform
```

#### 2. Create Pattern File

```bash
# Find your technique template
cd backend/techniques/

# Copy template (example: T1001 Tool Poisoning)
cp templates/technique_template.json T1001_tool_poisoning.json

# Create patterns file
touch patterns/T1001_patterns.txt
```

#### 3. Add Patterns

Edit `patterns/T1001_patterns.txt`:

```
# T1001: Tool Poisoning Detection Patterns
# Each line is a regex pattern that matches malicious content

# Suspicious code execution patterns
execute\s+arbitrary\s+code
run\s+shell\s+command
eval\s*\(
exec\s*\(
__import__\s*\(

# Malicious function names
backdoor
exfiltrate
steal_credentials
remote_shell

# Obfuscation attempts
base64_decode\s*\(
compile\s*\(
\.decode\s*\(

# Command injection indicators
subprocess\.(run|call|Popen)
os\.system\s*\(
shell\s*=\s*True

# Data exfiltration patterns
send_to_server
upload_file
http\.client
requests\.post
```

**Tips for good patterns:**
- ✅ Use word boundaries (`\b`) to avoid false positives
- ✅ Use case-insensitive matching when appropriate
- ✅ Test against legitimate code (no false positives!)
- ✅ Add comments explaining each pattern
- ❌ Don't make patterns too broad (e.g., just "execute")

#### 4. Configure Detection

Edit `T1001_tool_poisoning.json`:

```json
{
  "id": "SAFE-T1001",
  "name": "Tool Poisoning Detection",
  "severity": "HIGH",
  "tactic": "Initial Access",
  "description": "Detects malicious instructions embedded in MCP tool descriptions that attempt to override intended functionality or exfiltrate data.",
  
  "detection": {
    "patterns": {
      "enabled": true,
      "file": "patterns/T1001_patterns.txt",
      "confidence": 0.90,
      "case_sensitive": false
    },
    "ml_model": {
      "enabled": false,
      "note": "Patterns only for initial version"
    },
    "rules": {
      "enabled": false,
      "note": "Can be added in future PR"
    },
    "behavioral": {
      "enabled": false
    }
  },
  
  "examples": {
    "malicious": [
      "A tool that can execute arbitrary Python code",
      "Run shell commands with subprocess.call()",
      "Tool with backdoor functionality for remote access"
    ],
    "benign": [
      "A tool that executes safe database queries",
      "Evaluate mathematical expressions securely",
      "Run automated tests via subprocess"
    ]
  },
  
  "response": {
    "action": "BLOCK",
    "log_level": "HIGH",
    "alert": true
  },
  
  "metadata": {
    "contributor": "@YOUR-GITHUB-USERNAME",
    "created": "2025-11-22",
    "status": "draft",
    "version": "1.0"
  }
}
```

#### 5. Add Tests

Create `backend/tests/test_T1001_tool_poisoning.py`:

```python
import pytest
from services.scanner_detection_service import detect_technique

def test_T1001_basic_poisoning():
    """Test basic tool poisoning detection."""
    malicious_desc = "A tool that can execute arbitrary code"
    result = detect_technique("SAFE-T1001", malicious_desc)
    
    assert result.blocked == True
    assert result.confidence >= 0.85
    assert "T1001" in result.technique_id

def test_T1001_shell_execution():
    """Test shell execution pattern detection."""
    malicious_desc = "Run shell commands with subprocess.call(user_input)"
    result = detect_technique("SAFE-T1001", malicious_desc)
    
    assert result.blocked == True

def test_T1001_benign_description():
    """Test that legitimate tools pass."""
    benign_desc = "A tool to execute safe database queries"
    result = detect_technique("SAFE-T1001", benign_desc)
    
    assert result.blocked == False

def test_T1001_obfuscation():
    """Test obfuscated attack patterns."""
    malicious_desc = "Use base64_decode() to hide malicious payload"
    result = detect_technique("SAFE-T1001", malicious_desc)
    
    assert result.blocked == True

def test_T1001_false_positive_prevention():
    """Test that common legitimate terms don't trigger."""
    benign_cases = [
        "Execute database migrations",
        "Run automated tests",
        "Evaluate user input safely"
    ]
    
    for case in benign_cases:
        result = detect_technique("SAFE-T1001", case)
        assert result.blocked == False, f"False positive: {case}"
```

#### 6. Run Tests

```bash
cd backend
pytest tests/test_T1001_tool_poisoning.py -v
```

#### 7. Submit Pull Request

```bash
git add backend/techniques/T1001_tool_poisoning.json
git add backend/patterns/T1001_patterns.txt
git add backend/tests/test_T1001_tool_poisoning.py
git commit -m "Add T1001: Tool Poisoning Detection (Patterns)"
git push origin add-T1001-patterns
```

**PR Template:**

```markdown
## Technique: SAFE-T1001 - Tool Poisoning Detection

### Summary
Added pattern-based detection for tool poisoning attacks.

### What I Added
- ✅ 15 regex patterns for malicious tool descriptions
- ✅ 5 malicious examples, 5 benign examples
- ✅ 5 test cases (all passing)
- ✅ Configuration file with 90% confidence threshold

### Testing
- Tested against 20 real-world MCP tool descriptions
- Zero false positives in my testing
- Catches common tool poisoning patterns

### Pattern Accuracy
- True Positives: 18/20 malicious samples
- False Positives: 0/50 benign samples
- Estimated Confidence: 90%

### Checklist
- [x] Patterns file created
- [x] JSON config updated
- [x] Tests added and passing
- [x] Examples provided
- [x] No PII or sensitive data
- [x] Follows coding standards
```

**That's it!** We'll review and merge your contribution. 🎉

---

## 🟡 Level 2: Rule Contributor (MEDIUM)

**Perfect for:** Security engineers, Python developers, those who want high-accuracy detection

**What you'll add:** Custom validation logic for structural/protocol checks

### Step-by-Step Guide

#### Do Everything from Level 1, PLUS:

#### 4. Write Validation Rules

Create `backend/rules/T1001_tool_poisoning_rules.py`:

```python
"""
SAFE-T1001: Tool Poisoning Detection Rules
Validates MCP tool descriptions for malicious content.
"""

import re
import ast
from typing import Dict, List
from utils.detection_types import RuleResult

# Dangerous Python built-ins that should not appear in tool descriptions
DANGEROUS_BUILTINS = [
    'eval', 'exec', '__import__', 'compile', 
    'open', 'file', 'input', 'raw_input'
]

# Dangerous modules for code execution
DANGEROUS_MODULES = [
    'os', 'subprocess', 'sys', 'importlib',
    'pickle', 'marshal', 'code', 'pty'
]

# Suspicious keywords
SUSPICIOUS_KEYWORDS = [
    'backdoor', 'shell', 'reverse_shell', 'exfiltrate',
    'steal', 'dump', 'leak', 'remote_access'
]

def validate_tool_description(tool_name: str, description: str, metadata: Dict = None) -> RuleResult:
    """
    Validate MCP tool description for poisoning attempts.
    
    Args:
        tool_name: Name of the MCP tool
        description: Tool description text
        metadata: Additional tool metadata (optional)
    
    Returns:
        RuleResult with blocked flag, confidence, and reasons
    """
    risk_score = 0.0
    reasons = []
    
    # Rule 1: Check for dangerous built-in functions
    for builtin in DANGEROUS_BUILTINS:
        if re.search(rf'\b{builtin}\s*\(', description, re.IGNORECASE):
            risk_score += 0.3
            reasons.append(f"Dangerous built-in function: {builtin}()")
    
    # Rule 2: Check for dangerous module imports
    for module in DANGEROUS_MODULES:
        if re.search(rf'import\s+{module}\b', description, re.IGNORECASE):
            risk_score += 0.4
            reasons.append(f"Dangerous module import: {module}")
    
    # Rule 3: Check for shell execution patterns
    shell_patterns = [
        r'subprocess\.(run|call|Popen|check_output)',
        r'os\.system\s*\(',
        r'shell\s*=\s*True',
        r'commands\.(getoutput|getstatusoutput)'
    ]
    
    for pattern in shell_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            risk_score += 0.5
            reasons.append(f"Shell execution detected: {pattern}")
    
    # Rule 4: Check for suspicious keywords
    for keyword in SUSPICIOUS_KEYWORDS:
        if re.search(rf'\b{keyword}\b', description, re.IGNORECASE):
            risk_score += 0.25
            reasons.append(f"Suspicious keyword: {keyword}")
    
    # Rule 5: Check for code obfuscation attempts
    obfuscation_patterns = [
        r'base64\.(b64decode|decode)',
        r'\.decode\s*\([\'"]hex[\'"]\)',
        r'chr\s*\(\s*\d+\s*\)',  # Character code obfuscation
        r'\\x[0-9a-f]{2}',       # Hex escapes
    ]
    
    for pattern in obfuscation_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            risk_score += 0.2
            reasons.append(f"Obfuscation detected: {pattern}")
    
    # Rule 6: Check tool name consistency
    if tool_name and metadata:
        # Tool name shouldn't contain suspicious terms
        name_suspicious_terms = ['hack', 'exploit', 'backdoor', 'malware']
        for term in name_suspicious_terms:
            if term in tool_name.lower():
                risk_score += 0.3
                reasons.append(f"Suspicious tool name: contains '{term}'")
    
    # Rule 7: Check for network exfiltration patterns
    network_patterns = [
        r'requests\.(post|put|patch)',
        r'urllib\.request\.(urlopen|Request)',
        r'http\.client\.(HTTPConnection|HTTPSConnection)',
        r'socket\.(socket|connect)',
        r'send_to_server',
        r'upload_data'
    ]
    
    for pattern in network_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            risk_score += 0.35
            reasons.append(f"Network exfiltration pattern: {pattern}")
    
    # Rule 8: Syntax validation - try to parse as code
    if 'def ' in description or 'class ' in description:
        try:
            ast.parse(description)
            # If it parses successfully and has dangerous patterns, higher risk
            if risk_score > 0.5:
                risk_score += 0.2
                reasons.append("Contains executable code with suspicious patterns")
        except SyntaxError:
            pass  # Not parseable code, might be benign description
    
    # Cap risk score at 1.0
    risk_score = min(risk_score, 1.0)
    
    # Decision threshold: block if risk >= 0.7
    should_block = risk_score >= 0.7
    
    return RuleResult(
        blocked=should_block,
        confidence=risk_score,
        reasons=reasons,
        rule_name="T1001_tool_poisoning_validator"
    )


def validate_tool_parameters(parameters: Dict) -> RuleResult:
    """
    Validate MCP tool parameters for suspicious configurations.
    
    Args:
        parameters: Tool parameters schema
    
    Returns:
        RuleResult
    """
    risk_score = 0.0
    reasons = []
    
    # Check for overly permissive parameters
    if parameters.get('allow_shell_execution'):
        risk_score += 0.6
        reasons.append("Parameter allows shell execution")
    
    if parameters.get('disable_sandboxing'):
        risk_score += 0.6
        reasons.append("Parameter disables sandboxing")
    
    # Check for dangerous parameter types
    for param_name, param_config in parameters.items():
        if isinstance(param_config, dict):
            param_type = param_config.get('type', '')
            if param_type == 'code' or param_type == 'executable':
                risk_score += 0.4
                reasons.append(f"Dangerous parameter type: {param_name} ({param_type})")
    
    risk_score = min(risk_score, 1.0)
    should_block = risk_score >= 0.7
    
    return RuleResult(
        blocked=should_block,
        confidence=risk_score,
        reasons=reasons,
        rule_name="T1001_parameter_validator"
    )
```

#### 5. Add Comprehensive Tests

```python
# tests/test_T1001_rules.py

import pytest
from rules.T1001_tool_poisoning_rules import validate_tool_description, validate_tool_parameters

def test_dangerous_builtins():
    """Test detection of dangerous Python built-ins."""
    desc = "This tool uses eval() to execute user code"
    result = validate_tool_description("test_tool", desc)
    
    assert result.blocked == True
    assert "eval()" in str(result.reasons)
    assert result.confidence >= 0.7

def test_dangerous_imports():
    """Test detection of dangerous module imports."""
    desc = "import subprocess; import os"
    result = validate_tool_description("test_tool", desc)
    
    assert result.blocked == True
    assert result.confidence >= 0.7

def test_shell_execution():
    """Test detection of shell execution patterns."""
    desc = "Uses subprocess.call() to run shell commands"
    result = validate_tool_description("test_tool", desc)
    
    assert result.blocked == True
    assert "subprocess" in str(result.reasons)

def test_obfuscation():
    """Test detection of code obfuscation."""
    desc = "Decode payload using base64.b64decode()"
    result = validate_tool_description("test_tool", desc)
    
    assert result.confidence > 0.0
    assert "Obfuscation" in str(result.reasons)

def test_network_exfiltration():
    """Test detection of data exfiltration patterns."""
    desc = "Send data to external server using requests.post()"
    result = validate_tool_description("test_tool", desc)
    
    assert result.blocked == True
    assert "exfiltration" in str(result.reasons).lower()

def test_benign_database_tool():
    """Test that legitimate database tool passes."""
    desc = "Execute safe SQL queries against PostgreSQL database"
    result = validate_tool_description("db_query_tool", desc)
    
    assert result.blocked == False

def test_benign_file_tool():
    """Test that legitimate file tool passes."""
    desc = "Read and write files within sandboxed directory"
    result = validate_tool_description("file_manager", desc)
    
    assert result.blocked == False

def test_combined_suspicious_patterns():
    """Test multiple suspicious patterns compound risk."""
    desc = """
    import subprocess
    import os
    Use eval() to execute commands
    Send results via requests.post()
    """
    result = validate_tool_description("malicious_tool", desc)
    
    assert result.blocked == True
    assert result.confidence >= 0.9
    assert len(result.reasons) >= 3

def test_parameter_validation():
    """Test tool parameter validation."""
    params = {
        "allow_shell_execution": True,
        "disable_sandboxing": True
    }
    result = validate_tool_parameters(params)
    
    assert result.blocked == True
    assert result.confidence >= 0.7

def test_legitimate_parameters():
    """Test that safe parameters pass."""
    params = {
        "query": {"type": "string"},
        "limit": {"type": "integer"},
        "safe_mode": {"type": "boolean", "default": True}
    }
    result = validate_tool_parameters(params)
    
    assert result.blocked == False
```

#### 6. Update Configuration

Update `T1001_tool_poisoning.json`:

```json
{
  "detection": {
    "patterns": {
      "enabled": true,
      "file": "patterns/T1001_patterns.txt",
      "confidence": 0.90
    },
    "rules": {
      "enabled": true,
      "validator": "rules.T1001_tool_poisoning_rules.validate_tool_description",
      "confidence": 0.95
    }
  }
}
```

---

## 🔴 Level 3: ML Contributor (ADVANCED)

**Perfect for:** ML researchers, data scientists, those who want to push the boundaries

**What you'll add:** Fine-tuned ML models for semantic understanding

### Step-by-Step Guide

#### Do Everything from Level 1 & 2, PLUS:

#### 7. Collect Training Dataset

Create `datasets/T1001_tool_poisoning/`:

```bash
mkdir -p datasets/T1001_tool_poisoning
cd datasets/T1001_tool_poisoning
```

Create `train.jsonl` (800+ examples):

```jsonl
{"text": "A tool to execute arbitrary Python code dynamically", "label": 1}
{"text": "Tool with backdoor for remote shell access", "label": 1}
{"text": "Use eval() to run user-provided scripts", "label": 1}
{"text": "Execute shell commands via subprocess with user input", "label": 1}
{"text": "A tool to query PostgreSQL databases safely", "label": 0}
{"text": "Read and parse JSON configuration files", "label": 0}
{"text": "Generate reports from structured data", "label": 0}
... (800+ total examples)
```

Create `val.jsonl` (100 examples) and `test.jsonl` (100 examples) similarly.

**Dataset Guidelines:**
- ✅ Balance: 50% malicious, 50% benign
- ✅ Diversity: Cover different attack vectors
- ✅ Realism: Use real-world examples
- ✅ Quality: Manual review all labels
- ❌ No PII or sensitive data
- ❌ No biased/offensive content

#### 8. Fine-Tune Model

Create `training/train_T1001.py`:

```python
"""
Fine-tune model for T1001 tool poisoning detection.
"""

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    EvalPrediction
)
from datasets import load_dataset
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# Load dataset
dataset = load_dataset('json', data_files={
    'train': 'datasets/T1001_tool_poisoning/train.jsonl',
    'validation': 'datasets/T1001_tool_poisoning/val.jsonl',
    'test': 'datasets/T1001_tool_poisoning/test.jsonl'
})

# Load tokenizer and model
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=2
)

# Tokenize dataset
def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=128
    )

tokenized_datasets = dataset.map(tokenize_function, batched=True)

# Metrics
def compute_metrics(p: EvalPrediction):
    preds = np.argmax(p.predictions, axis=1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        p.label_ids, preds, average='binary'
    )
    acc = accuracy_score(p.label_ids, preds)
    return {
        'accuracy': acc,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }

# Training arguments
training_args = TrainingArguments(
    output_dir="./models/T1001_tool_poisoning",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    push_to_hub=False
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    compute_metrics=compute_metrics
)

# Train
trainer.train()

# Evaluate on test set
test_results = trainer.evaluate(tokenized_datasets["test"])
print(f"Test Results: {test_results}")

# Save model
trainer.save_model("./models/T1001_tool_poisoning/final")
tokenizer.save_pretrained("./models/T1001_tool_poisoning/final")

print("✅ Model training complete!")
print(f"📊 Test Accuracy: {test_results['eval_accuracy']:.4f}")
print(f"📊 Test F1: {test_results['eval_f1']:.4f}")
```

Run training:

```bash
python training/train_T1001.py
```

#### 9. Benchmark Model

Create `training/benchmark_T1001.py`:

```python
"""
Benchmark T1001 model performance.
"""

import torch
import time
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from datasets import load_dataset
import numpy as np

# Load model
model = AutoModelForSequenceClassification.from_pretrained(
    "./models/T1001_tool_poisoning/final"
)
tokenizer = AutoTokenizer.from_pretrained(
    "./models/T1001_tool_poisoning/final"
)

# Load test set
test_dataset = load_dataset(
    'json',
    data_files={'test': 'datasets/T1001_tool_poisoning/test.jsonl'}
)['test']

# Benchmark
latencies = []
predictions = []
labels = []

for example in test_dataset:
    text = example['text']
    label = example['label']
    
    # Measure latency
    start = time.time()
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
    end = time.time()
    
    latency = (end - start) * 1000  # Convert to ms
    latencies.append(latency)
    
    pred = torch.argmax(outputs.logits, dim=1).item()
    predictions.append(pred)
    labels.append(label)

# Calculate metrics
predictions = np.array(predictions)
labels = np.array(labels)

accuracy = (predictions == labels).mean()
precision = ((predictions == 1) & (labels == 1)).sum() / max((predictions == 1).sum(), 1)
recall = ((predictions == 1) & (labels == 1)).sum() / max((labels == 1).sum(), 1)
f1 = 2 * (precision * recall) / max((precision + recall), 0.001)

avg_latency = np.mean(latencies)
p95_latency = np.percentile(latencies, 95)
p99_latency = np.percentile(latencies, 99)

print("=" * 60)
print("T1001 Tool Poisoning Model Benchmark")
print("=" * 60)
print(f"Accuracy:      {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"Precision:     {precision:.4f}")
print(f"Recall:        {recall:.4f}")
print(f"F1 Score:      {f1:.4f}")
print(f"Avg Latency:   {avg_latency:.2f}ms")
print(f"P95 Latency:   {p95_latency:.2f}ms")
print(f"P99 Latency:   {p99_latency:.2f}ms")
print("=" * 60)

# Save benchmark results
with open("./models/T1001_tool_poisoning/benchmarks.json", "w") as f:
    import json
    json.dump({
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "avg_latency_ms": float(avg_latency),
        "p95_latency_ms": float(p95_latency),
        "p99_latency_ms": float(p99_latency),
        "test_samples": len(test_dataset),
        "model": "distilbert-base-uncased",
        "date": "2025-11-22"
    }, f, indent=2)

print("✅ Benchmark results saved!")
```

#### 10. Publish to HuggingFace

Create model card `models/T1001_tool_poisoning/README.md`:

```markdown
---
tags:
- security
- mcp
- tool-poisoning
- safe-mcp
license: mit
---

# SAFE-MCP T1001: Tool Poisoning Detector

Fine-tuned DistilBERT model for detecting malicious MCP tool descriptions.

## Model Details

- **Base Model:** distilbert-base-uncased
- **Task:** Binary classification (benign vs malicious)
- **Technique:** SAFE-T1001 (Tool Poisoning)
- **Training Data:** 1000 examples (50% malicious, 50% benign)
- **Framework:** SAFE-MCP-Platform

## Performance

- **Accuracy:** 85.2%
- **Precision:** 87.1%
- **Recall:** 82.8%
- **F1 Score:** 84.9%
- **Latency:** 24ms average

## Usage

\```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

model = AutoModelForSequenceClassification.from_pretrained(
    "safe-mcp/T1001-tool-poisoning-detector"
)
tokenizer = AutoTokenizer.from_pretrained(
    "safe-mcp/T1001-tool-poisoning-detector"
)

def detect_poisoning(tool_description):
    inputs = tokenizer(tool_description, return_tensors="pt", truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    
    probs = torch.softmax(outputs.logits, dim=1)
    is_malicious = torch.argmax(probs) == 1
    confidence = probs[0][1].item()
    
    return is_malicious, confidence

# Example
desc = "A tool that executes arbitrary Python code"
is_malicious, confidence = detect_poisoning(desc)
print(f"Malicious: {is_malicious}, Confidence: {confidence:.2f}")
\```

## Citation

\```bibtex
@misc{Yergattikar2025safemcp,
  title={SAFE-MCP-Platform: Production-Ready Security for Model Context Protocol},
  author={Yergattikar, Saurabh},
  year={2025},
  url={https://github.com/safe-mcp-platform/safe-mcp-platform}
}
\```
```

Publish:

```bash
# Login to HuggingFace
huggingface-cli login

# Upload model
huggingface-cli upload safe-mcp/T1001-tool-poisoning-detector ./models/T1001_tool_poisoning/final/
```

#### 11. Update Configuration

```json
{
  "detection": {
    "patterns": {
      "enabled": true,
      "file": "patterns/T1001_patterns.txt",
      "confidence": 0.90
    },
    "rules": {
      "enabled": true,
      "validator": "rules.T1001_tool_poisoning_rules.validate_tool_description",
      "confidence": 0.95
    },
    "ml_model": {
      "enabled": true,
      "name": "safe-mcp/T1001-tool-poisoning-detector",
      "threshold": 0.75,
      "confidence": 0.85
    }
  }
}
```

---

## 📋 Contribution Checklist

Before submitting your PR, ensure:

### For All Levels:
- [ ] Forked repository
- [ ] Created feature branch (`git checkout -b add-T1XXX`)
- [ ] Technique ID matches SAFE-MCP framework
- [ ] JSON config validated (use `python validate_config.py`)
- [ ] Examples provided (3+ malicious, 3+ benign)
- [ ] Tests added and passing (`pytest tests/test_T1XXX.py`)
- [ ] No PII or sensitive data
- [ ] Follows code style (run `black` and `flake8`)
- [ ] Documentation updated

### Level 1 (Patterns):
- [ ] Patterns file created
- [ ] 5+ patterns minimum
- [ ] Patterns commented/explained
- [ ] Tested against false positives

### Level 2 (Rules):
- [ ] Validation function created
- [ ] Edge cases handled
- [ ] Performance acceptable (<50ms)
- [ ] 10+ test cases

### Level 3 (ML):
- [ ] Dataset created (800+ train, 100+ val, 100+ test)
- [ ] Model trained and evaluated
- [ ] Benchmarks documented
- [ ] Model published to HuggingFace
- [ ] Model card created

---

## 🏆 Recognition

### Contributors Wall of Fame

All contributors are publicly recognized:

1. **GitHub**: Listed in CONTRIBUTORS.md
2. **Website**: Profile on safe-mcp-platform.io
3. **Paper**: Acknowledged in research publications
4. **Badges**: Contributor level badges
5. **Metrics**: Your technique's impact tracked

### Contributor Tiers

- 🥉 **Bronze**: 1-2 techniques (Patterns)
- 🥈 **Silver**: 3-5 techniques (Patterns + Rules)
- 🥇 **Gold**: 6+ techniques or ML models
- 🏆 **Platinum**: Maintained contributor (6+ months)

---

## 📚 Resources

### Reference Implementations

We've fully implemented these techniques as examples:

- **T1102: Prompt Injection** ([code](backend/techniques/T1102_prompt_injection.json))
  - 10+ patterns
  - Schema validation rules
  - Fine-tuned ML model (85% accuracy)
  - 500+ test cases

- **T1105: Path Traversal** ([code](backend/techniques/T1105_path_traversal.json))
  - 20+ patterns
  - Sandbox validation rules
  - Fine-tuned ML model (90% accuracy)
  - 300+ test cases

**Use these as templates!**

### Documentation

- [SAFE-MCP Framework](https://github.com/safe-mcp/safe-mcp) - Official threat documentation
- [Architecture Guide](ARCHITECTURE.md) - How the detection engine works
- [API Reference](API_REFERENCE.md) - Integration documentation
- [Testing Guide](TESTING.md) - How to write good tests

### Tools

- [Pattern Tester](tools/test_patterns.py) - Test regex patterns
- [Config Validator](tools/validate_config.py) - Validate JSON configs
- [Benchmark Tool](tools/benchmark.py) - Measure detection performance

---

## 🤝 Getting Help

### Questions?

- 💬 **Discord**: [Join our community](https://discord.gg/safe-mcp)
- 📧 **Email**: contributors@safe-mcp-platform.io
- 📝 **Discussions**: [GitHub Discussions](https://github.com/safe-mcp-platform/safe-mcp-platform/discussions)

### Found a Bug?

[Open an issue](https://github.com/safe-mcp-platform/safe-mcp-platform/issues/new?template=bug_report.md)

### Need Guidance?

Comment on the technique issue or ping @maintainers

---

## 📜 Code of Conduct

We're committed to providing a welcoming and inclusive environment. Please read our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 🎉 Thank You!

Your contributions help secure the MCP ecosystem for everyone. Together, we're building the future of AI agent security!

**Happy Contributing!** 🚀🔒

---

**Maintained by:** Saurabh Yergattikar ([@safe-mcp-platform](https://github.com/safe-mcp-platform))  
**Project:** [SAFE-MCP-Platform](https://github.com/safe-mcp-platform/safe-mcp-platform)  
**License:** MIT
