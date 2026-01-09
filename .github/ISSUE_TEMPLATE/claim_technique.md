---
name: 🎯 Claim a Technique
about: Claim an MCP attack technique to implement
title: '[TECHNIQUE] SAFE-TXXXX: Technique Name'
labels: 'help-wanted, good-first-issue'
assignees: ''
---

## 🎯 Technique Information

**Technique ID:** SAFE-TXXXX  
**Technique Name:** [Name from MCP Attack Taxonomy]  
**Tactic:** [MITRE ATT&CK Tactic]  
**Severity:** CRITICAL / HIGH / MEDIUM / LOW  

**SAFE-MCP Reference:** https://github.com/safe-mcp/safe-mcp/blob/main/techniques/TXXXX.md

---

## 📋 What This Technique Detects

[Brief description of the attack vector]

**Example Attack:**
```
[Example of malicious input]
```

**Legitimate Use Case (should NOT be blocked):**
```
[Example of benign input]
```

---

## 🛠️ Implementation Levels

Choose which level you want to contribute:

### 🟢 Level 1: Patterns Only (EASIEST - 2-4 hours)
- [ ] Add 5+ regex patterns
- [ ] Create `patterns/TXXXX_patterns.txt`
- [ ] Update `techniques/TXXXX.json`
- [ ] Add 3+ examples (malicious & benign)
- [ ] Write 5+ test cases

**Perfect for:** Beginners, students, first-time contributors

---

### 🟡 Level 2: Patterns + Rules (MEDIUM - 6-10 hours)
- [ ] Everything from Level 1
- [ ] Write validation rules in `rules/TXXXX_rules.py`
- [ ] Add structural/protocol checks
- [ ] Write 10+ test cases
- [ ] Performance benchmarks

**Perfect for:** Security engineers, Python developers

---

### 🔴 Level 3: Full Stack (ADVANCED - 2-4 weeks)
- [ ] Everything from Level 1 & 2
- [ ] Collect training dataset (800+ examples)
- [ ] Fine-tune ML model
- [ ] Publish to HuggingFace
- [ ] Write 20+ test cases
- [ ] Comprehensive benchmarks

**Perfect for:** ML researchers, data scientists

---

## 📚 Resources

### Reference Implementations
- **T1102 (Prompt Injection)**: [techniques/T1102_prompt_injection.json](../backend/techniques/T1102_prompt_injection.json)
- **T1105 (Path Traversal)**: [techniques/T1105_path_traversal.json](../backend/techniques/T1105_path_traversal.json)

### Templates
- **Technique Config**: [templates/technique_template.json](../backend/techniques/templates/technique_template.json)
- **Pattern File**: See T1102_patterns.txt or T1105_patterns.txt
- **Rules File**: See T1102_rules.py or T1105_rules.py

### Guides
- **Contribution Guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Testing Guide**: [TESTING.md](../TESTING.md)
- **Architecture**: [ARCHITECTURE.md](../ARCHITECTURE.md)

---

## 🎯 How to Claim This Technique

1. **Comment below** with:
   - Which level you're implementing (1, 2, or 3)
   - Estimated completion time
   - Any questions you have

2. **We'll assign you** (technique marked as "In Progress")

3. **Fork the repo** and create your branch:
   ```bash
   git checkout -b add-TXXXX-detection
   ```

4. **Implement & submit PR** following the [contribution guide](../CONTRIBUTING.md)

---

## ✅ Acceptance Criteria

### Minimum Requirements (All Levels):
- [ ] Technique config file created (`techniques/TXXXX.json`)
- [ ] At least 3 malicious examples
- [ ] At least 3 benign examples
- [ ] Tests added and passing
- [ ] No false positives in provided examples
- [ ] Follows JSON schema
- [ ] Documentation updated

### Level 1 (Patterns):
- [ ] Minimum 5 regex patterns
- [ ] Patterns file created and linked
- [ ] Patterns commented/explained
- [ ] False positive testing done

### Level 2 (Rules):
- [ ] Validation function implemented
- [ ] Edge cases handled
- [ ] Performance < 50ms
- [ ] 10+ test cases

### Level 3 (ML):
- [ ] Dataset created (min 800 train, 100 val, 100 test)
- [ ] Model trained and evaluated
- [ ] Accuracy > 75%
- [ ] Model published to HuggingFace
- [ ] Model card created
- [ ] Benchmark results documented

---

## 💡 Tips for Success

### Finding Patterns
- Review the MCP attack technique documentation
- Search for real-world examples on GitHub
- Check security advisories and CVEs
- Ask in Discord if you need help!

### Testing
```bash
# Run your tests
cd backend
pytest tests/test_TXXXX.py -v

# Validate your config
python tools/validate_config.py techniques/TXXXX.json

# Benchmark performance
python tools/benchmark.py TXXXX
```

### Getting Help
- 💬 **Discord**: [#contributors channel]( )
- 📧 **Email**: 
- 💭 **Ask in comments**: We're here to help!

---

## 🏆 Recognition

Upon successful merge, you'll get:
- ✅ Listed in [CONTRIBUTORS.md](../CONTRIBUTORS.md)
- ✅ GitHub contributor badge
- ✅ Technique ownership credit
- ✅ Impact metrics tracking (attacks blocked)
- ✅ Acknowledgment in research papers

---

## 📊 Difficulty Rating

**Estimated Difficulty:** ⭐⭐⭐ (1=Easy, 5=Very Hard)

**Why this rating:**
[Explanation of why this technique is easy/medium/hard to implement]

**Prerequisites:**
- [ ] Understanding of [specific concept]
- [ ] Knowledge of [specific technology]
- [ ] Familiarity with [specific attack vector]

---

## 🚀 Let's Do This!

Comment below to claim this technique and join the mission to secure MCP! 💪🛡️

---

**Questions?** Drop them in the comments or join our [Discord]( )!

