# Attack Simulations

This directory contains test cases for various SAFE-MCP attack techniques.

## Running Simulations

```bash
cd /Users/saurabh_sharmila_nysa_mac/Desktop/Saurabh_OSS/safe-mcp-platform

# Run all simulations
python3 tests/run_simulations.py

# Run specific simulation
python3 tests/run_simulations.py tests/attack_simulations/01_prompt_injection.json
```

## Attack Categories

### Initial Access (T1001-T1099)
- `01_prompt_injection.json` - Prompt manipulation
- `04_social_engineering.json` - Social engineering attempts

### Execution (T1101-T1199)
- `03_command_injection.json` - OS command injection
- `05_code_execution.json` - Arbitrary code execution

### Discovery (T1601-T1699)
- `02_path_traversal.json` - File system discovery
- `06_enumeration.json` - System enumeration

## Creating New Simulations

Use this template:

```json
{
  "attack_name": "Attack Name",
  "technique_id": "SAFE-T####",
  "severity": "HIGH|MEDIUM|LOW|CRITICAL",
  "description": "What this attack does",
  "mcp_message": {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "tool_name",
      "arguments": {}
    },
    "id": 1
  },
  "expected_detection": true,
  "expected_risk_level": "HIGH",
  "expected_action": "BLOCK"
}
```

