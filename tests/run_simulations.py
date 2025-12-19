"""
Attack Simulation Runner

Run all attack simulations and verify detection accuracy.
"""
import sys
import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.dynamic_detection_engine import detection_engine
from services.mcp_protocol_parser import MCPProtocolParser


class SimulationRunner:
    """Run attack simulations and verify results"""
    
    def __init__(self):
        self.parser = MCPProtocolParser()
        self.passed = 0
        self.failed = 0
        self.results = []
    
    async def run_simulation(self, simulation_file: Path) -> Dict:
        """Run a single simulation"""
        print(f"\n{'='*60}")
        print(f"🎯 Running: {simulation_file.name}")
        print(f"{'='*60}")
        
        # Load simulation
        with open(simulation_file, 'r') as f:
            sim = json.load(f)
        
        print(f"Attack: {sim['attack_name']}")
        print(f"Technique: {sim['technique_id']}")
        print(f"Severity: {sim['severity']}")
        
        # Parse MCP message
        mcp_msg = self.parser.parse(sim['mcp_message'])
        
        # Run detection
        result = await detection_engine.detect_all(mcp_msg, None)
        
        # Verify results
        detection_match = result.matched_techniques != [] if sim['expected_detection'] else result.matched_techniques == []
        risk_match = result.overall_risk_level == sim.get('expected_risk_level', 'NONE')
        action_match = result.action == sim.get('expected_action', 'ALLOW')
        
        passed = detection_match and (risk_match or not sim['expected_detection'])
        
        # Print results
        print(f"\n📊 Detection Results:")
        print(f"   Risk Level: {result.overall_risk_level} (expected: {sim.get('expected_risk_level', 'N/A')})")
        print(f"   Action: {result.action} (expected: {sim.get('expected_action', 'N/A')})")
        print(f"   Matched: {len(result.matched_techniques)} techniques")
        
        if result.matched_techniques:
            for match in result.matched_techniques[:3]:  # Top 3
                print(f"      • {match.technique_id} - {match.technique_name} ({match.confidence:.2f})")
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}")
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        return {
            "simulation": sim['attack_name'],
            "passed": passed,
            "detected": len(result.matched_techniques) > 0,
            "risk_level": result.overall_risk_level,
            "action": result.action
        }
    
    async def run_all(self, simulations_dir: Path):
        """Run all simulations in directory"""
        print("=" * 60)
        print("🧪 SAFE-MCP Attack Simulation Suite")
        print("=" * 60)
        print(f"Techniques loaded: {len(detection_engine.techniques)}")
        print(f"Simulations directory: {simulations_dir}")
        
        # Find all JSON files
        sim_files = sorted(simulations_dir.glob("*.json"))
        
        if not sim_files:
            print(f"\n❌ No simulation files found in {simulations_dir}")
            return
        
        print(f"Found {len(sim_files)} simulations\n")
        
        # Run each simulation
        for sim_file in sim_files:
            try:
                result = await self.run_simulation(sim_file)
                self.results.append(result)
            except Exception as e:
                print(f"❌ Error running {sim_file.name}: {e}")
                self.failed += 1
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 SIMULATION SUMMARY")
        print("=" * 60)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.results:
            status = "✅" if result['passed'] else "❌"
            detected = "🛡️ " if result['detected'] else "   "
            print(f"{status} {detected}{result['simulation']}")
            print(f"      Risk: {result['risk_level']}, Action: {result['action']}")
        
        print("\n" + "=" * 60)
        
        if self.failed == 0:
            print("✨ All simulations passed!")
        else:
            print(f"⚠️  {self.failed} simulation(s) failed")


async def main():
    """Main entry point"""
    # Determine simulations directory
    if len(sys.argv) > 1:
        # Run specific simulation
        sim_file = Path(sys.argv[1])
        if not sim_file.exists():
            print(f"❌ Simulation file not found: {sim_file}")
            sys.exit(1)
        
        runner = SimulationRunner()
        await runner.run_simulation(sim_file)
    else:
        # Run all simulations
        simulations_dir = Path(__file__).parent / "attack_simulations"
        runner = SimulationRunner()
        await runner.run_all(simulations_dir)


if __name__ == "__main__":
    asyncio.run(main())

