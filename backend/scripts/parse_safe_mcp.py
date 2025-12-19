"""
Parse SAFE-MCP repository and extract techniques and mitigations.
Converts markdown documentation into structured JSON configurations.
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional
import sys


class SAFEMCPParser:
    """Parser for SAFE-MCP repository"""
    
    def __init__(self, safe_mcp_repo_path: str):
        self.repo_path = Path(safe_mcp_repo_path)
        self.techniques_dir = self.repo_path / "techniques"
        self.mitigations_dir = self.repo_path / "mitigations"
        
        if not self.repo_path.exists():
            raise ValueError(f"SAFE-MCP repository not found at: {self.repo_path}")
    
    def parse_all_techniques(self) -> Dict[str, dict]:
        """Parse all SAFE-T* techniques from the repository"""
        techniques = {}
        
        print(f"📁 Scanning techniques directory: {self.techniques_dir}")
        
        if not self.techniques_dir.exists():
            print(f"❌ Techniques directory not found: {self.techniques_dir}")
            return techniques
        
        # Find all SAFE-T* directories
        for tech_dir in sorted(self.techniques_dir.iterdir()):
            if not tech_dir.is_dir():
                continue
            
            if not tech_dir.name.startswith("SAFE-T"):
                continue
            
            try:
                technique = self.parse_technique(tech_dir)
                if technique:
                    techniques[technique["id"]] = technique
                    print(f"✅ Parsed: {technique['id']} - {technique['name']}")
            except Exception as e:
                print(f"⚠️  Error parsing {tech_dir.name}: {e}")
        
        print(f"\n✅ Total techniques parsed: {len(techniques)}")
        return techniques
    
    def parse_technique(self, tech_dir: Path) -> Optional[dict]:
        """Parse a single SAFE-T technique from its README.md"""
        readme_path = tech_dir / "README.md"
        
        if not readme_path.exists():
            return None
        
        content = readme_path.read_text(encoding='utf-8')
        technique_id = tech_dir.name
        
        # Extract information using regex
        technique = {
            "id": technique_id,
            "name": self.extract_title(content),
            "tactic": self.extract_tactic(content, technique_id),
            "description": self.extract_section(content, "Description"),
            "examples": self.extract_examples(content),
            "detection_guidance": self.extract_section(content, "Detection"),
            "mitigations": self.extract_mitigations_list(content),
            "mitre_mappings": self.extract_mitre_mappings(content),
            "severity": self.determine_severity(technique_id),
            "enabled": True,
            
            # Detection configuration (to be filled in)
            "detection": self.determine_detection_config(content, technique_id)
        }
        
        return technique
    
    def extract_title(self, content: str) -> str:
        """Extract technique name from markdown"""
        match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Unknown Technique"
    
    def extract_tactic(self, content: str, technique_id: str) -> str:
        """Determine tactic category from technique ID"""
        # SAFE-T technique ID mapping to tactics
        tactic_ranges = {
            "Initial Access": range(1001, 1100),
            "Execution": range(1101, 1200),
            "Persistence": range(1201, 1300),
            "Privilege Escalation": range(1301, 1400),
            "Defense Evasion": range(1401, 1500),
            "Credential Access": range(1501, 1600),
            "Discovery": range(1601, 1700),
            "Lateral Movement": range(1701, 1800),
            "Collection": range(1801, 1900),
            "Command and Control": range(1901, 2000),
            "Exfiltration": range(2001, 2100),
            "Impact": range(2101, 2200),
            "Resource Development": range(3001, 3100),
            "Reconnaissance": range(3101, 3200),
        }
        
        # Extract number from SAFE-T####
        match = re.search(r'SAFE-T(\d+)', technique_id)
        if match:
            tech_num = int(match.group(1))
            for tactic, num_range in tactic_ranges.items():
                if tech_num in num_range:
                    return tactic
        
        # Try to extract from content
        tactic_match = re.search(r'\*\*Tactic[s]?\*\*:?\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if tactic_match:
            return tactic_match.group(1).strip()
        
        return "Unknown"
    
    def extract_section(self, content: str, section_name: str) -> str:
        """Extract a markdown section by heading"""
        # Try ## heading first
        pattern = rf'##\s+{section_name}\s*\n+(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not match:
            # Try **bold** format
            pattern = rf'\*\*{section_name}\*\*:?\s*\n+(.*?)(?=\n\*\*|\n##|\Z)'
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        return ""
    
    def extract_examples(self, content: str) -> List[str]:
        """Extract examples from the technique"""
        examples_text = self.extract_section(content, "Example")
        if not examples_text:
            examples_text = self.extract_section(content, "Examples")
        
        if not examples_text:
            return []
        
        # Split by bullet points or numbered lists
        lines = examples_text.split('\n')
        examples = []
        
        for line in lines:
            line = line.strip()
            # Remove bullet points, numbers
            line = re.sub(r'^[-*•]\s*', '', line)
            line = re.sub(r'^\d+\.\s*', '', line)
            
            if line and len(line) > 10:
                examples.append(line)
        
        return examples[:5]  # Limit to top 5 examples
    
    def extract_mitigations_list(self, content: str) -> List[str]:
        """Extract list of mitigation IDs"""
        mitigations = []
        
        # Look for SAFE-M-## references
        safe_m_matches = re.findall(r'(SAFE-M-\d+)', content)
        mitigations.extend(safe_m_matches)
        
        return list(set(mitigations))  # Deduplicate
    
    def extract_mitre_mappings(self, content: str) -> List[str]:
        """Extract MITRE ATT&CK technique mappings"""
        mappings = []
        
        # Look for T#### references
        mitre_matches = re.findall(r'\b(T\d{4}(?:\.\d{3})?)\b', content)
        mappings.extend(mitre_matches)
        
        return list(set(mappings))
    
    def determine_severity(self, technique_id: str) -> str:
        """Determine severity based on technique ID and tactic"""
        # High-risk tactics
        high_risk_prefixes = ["SAFE-T15", "SAFE-T17", "SAFE-T21"]  # WMD, Sexual Crimes, Impact
        if any(technique_id.startswith(p) for p in high_risk_prefixes):
            return "CRITICAL"
        
        # Extract number
        match = re.search(r'SAFE-T(\d+)', technique_id)
        if match:
            num = int(match.group(1))
            
            # Initial Access, Execution, Privilege Escalation = HIGH
            if num < 1400:
                return "HIGH"
            
            # Most others = MEDIUM
            if num < 2100:
                return "MEDIUM"
            
            # Impact, Resource Development = HIGH
            return "HIGH"
        
        return "MEDIUM"
    
    def determine_detection_config(self, content: str, technique_id: str) -> dict:
        """Determine optimal detection method for this technique"""
        content_lower = content.lower()
        
        # Default detection config
        config = {
            "method": "hybrid",
            "enabled": True
        }
        
        # Check if pattern matching is suitable
        patterns = []
        
        # Look for quoted strings in examples (potential patterns)
        pattern_matches = re.findall(r'"([^"]+)"', content)
        patterns.extend(pattern_matches[:10])
        
        # Look for code blocks
        code_matches = re.findall(r'`([^`]+)`', content)
        patterns.extend([c for c in code_matches if len(c) > 3][:5])
        
        if patterns:
            config["patterns"] = [
                {
                    "type": "substring" if len(p) < 50 else "regex",
                    "pattern": p,
                    "case_sensitive": False,
                    "weight": 0.8
                }
                for p in patterns[:5]
            ]
        
        # Determine if ML model would be beneficial
        # Complex attacks benefit from ML
        complex_indicators = [
            "context", "semantic", "intent", "obfuscation", 
            "sophisticated", "advanced", "evasion"
        ]
        
        if any(indicator in content_lower for indicator in complex_indicators):
            config["ml_model"] = {
                "enabled": True,
                "model_id": f"safe-mcp/{technique_id.lower()}-detector",
                "threshold": 0.75,
                "weight": 1.0
            }
        
        # Behavioral detection for rate/frequency attacks
        behavioral_indicators = ["rate", "frequency", "repeated", "burst", "flood", "dos"]
        if any(indicator in content_lower for indicator in behavioral_indicators):
            config["behavioral"] = {
                "enabled": True,
                "rules": [
                    {
                        "feature": "request_rate",
                        "check": "anomaly_detection",
                        "threshold": 10.0
                    }
                ]
            }
        
        # Rule-based for structural/protocol violations
        rule_indicators = ["invalid", "malformed", "protocol", "structure", "format"]
        if any(indicator in content_lower for indicator in rule_indicators):
            config["rules"] = [
                {
                    "type": "mcp_structure",
                    "check": "validation",
                    "condition": "is_valid_mcp_message"
                }
            ]
        
        return config
    
    def parse_all_mitigations(self) -> Dict[str, dict]:
        """Parse all SAFE-M* mitigations"""
        mitigations = {}
        
        print(f"\n📁 Scanning mitigations directory: {self.mitigations_dir}")
        
        if not self.mitigations_dir.exists():
            print(f"❌ Mitigations directory not found: {self.mitigations_dir}")
            return mitigations
        
        for mit_dir in sorted(self.mitigations_dir.iterdir()):
            if not mit_dir.is_dir():
                continue
            
            if not mit_dir.name.startswith("SAFE-M-"):
                continue
            
            try:
                mitigation = self.parse_mitigation(mit_dir)
                if mitigation:
                    mitigations[mitigation["id"]] = mitigation
                    print(f"✅ Parsed: {mitigation['id']} - {mitigation['name']}")
            except Exception as e:
                print(f"⚠️  Error parsing {mit_dir.name}: {e}")
        
        print(f"\n✅ Total mitigations parsed: {len(mitigations)}")
        return mitigations
    
    def parse_mitigation(self, mit_dir: Path) -> Optional[dict]:
        """Parse a single SAFE-M mitigation"""
        readme_path = mit_dir / "README.md"
        
        if not readme_path.exists():
            return None
        
        content = readme_path.read_text(encoding='utf-8')
        mitigation_id = mit_dir.name
        
        mitigation = {
            "id": mitigation_id,
            "name": self.extract_title(content),
            "description": self.extract_section(content, "Description"),
            "implementation": self.extract_section(content, "Implementation"),
            "techniques_mitigated": self.extract_techniques_list(content),
            "effectiveness": "HIGH",  # Default
            "enabled": True
        }
        
        return mitigation
    
    def extract_techniques_list(self, content: str) -> List[str]:
        """Extract list of technique IDs that this mitigation addresses"""
        techniques = []
        
        # Look for SAFE-T#### references
        tech_matches = re.findall(r'(SAFE-T\d+)', content)
        techniques.extend(tech_matches)
        
        return list(set(techniques))


def main():
    """Main execution"""
    # Get SAFE-MCP repository path
    safe_mcp_path = os.getenv(
        'SAFE_MCP_REPO',
        '/Users/saurabh_sharmila_nysa_mac/Desktop/Saurabh_OSS/safe-mcp'
    )
    
    print(f"🚀 SAFE-MCP Parser")
    print(f"📂 Repository path: {safe_mcp_path}\n")
    
    parser = SAFEMCPParser(safe_mcp_path)
    
    # Parse techniques
    print("=" * 60)
    print("PARSING TECHNIQUES")
    print("=" * 60)
    techniques = parser.parse_all_techniques()
    
    # Parse mitigations
    print("\n" + "=" * 60)
    print("PARSING MITIGATIONS")
    print("=" * 60)
    mitigations = parser.parse_all_mitigations()
    
    # Save to JSON
    output_dir = Path("backend/safe_mcp_data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    techniques_file = output_dir / "techniques.json"
    mitigations_file = output_dir / "mitigations.json"
    
    print("\n" + "=" * 60)
    print("SAVING OUTPUT")
    print("=" * 60)
    
    with open(techniques_file, 'w', encoding='utf-8') as f:
        json.dump(techniques, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved techniques to: {techniques_file}")
    
    with open(mitigations_file, 'w', encoding='utf-8') as f:
        json.dump(mitigations, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved mitigations to: {mitigations_file}")
    
    # Save individual technique files for dynamic loading
    techniques_dir = output_dir / "techniques"
    techniques_dir.mkdir(exist_ok=True)
    
    for tech_id, tech_data in techniques.items():
        tech_file = techniques_dir / f"{tech_id}.json"
        with open(tech_file, 'w', encoding='utf-8') as f:
            json.dump(tech_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(techniques)} individual technique files to: {techniques_dir}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"📊 Techniques parsed: {len(techniques)}")
    print(f"📊 Mitigations parsed: {len(mitigations)}")
    print(f"\n✨ SAFE-MCP data parsing complete!")


if __name__ == "__main__":
    main()

