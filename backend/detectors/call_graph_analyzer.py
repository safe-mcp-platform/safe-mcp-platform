"""
Call Graph Behavioral Analyzer (NOVEL - Channel 4)

Innovation: First graph-based behavioral analysis system for MCP.
Models MCP sessions as directed graphs to detect multi-stage attacks
that single-call analysis misses.

Unlike traditional behavioral analysis that tracks counts/rates,
this system:
- Builds call graphs showing tool call relationships
- Detects attack patterns spanning multiple calls
- Uses Graph Neural Networks for pattern recognition
- Identifies reconnaissance → exploitation → exfiltration chains

Technical Innovation:
- MCP session as directed graph
- Graph-based attack pattern matching
- GNN for novel attack detection
- Temporal-spatial analysis

Author: Saurabh Yergattikar
"""

import networkx as nx
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import structlog
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = structlog.get_logger()


class CallType(Enum):
    """Types of MCP calls"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    SYSTEM = "system"
    QUERY = "query"


class AttackStage(Enum):
    """Stages in multi-stage attacks"""
    RECONNAISSANCE = "reconnaissance"
    EXPLOITATION = "exploitation"
    EXFILTRATION = "exfiltration"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"


@dataclass
class MCPCallNode:
    """Node in call graph representing a single MCP call"""
    call_id: str
    timestamp: datetime
    tool: str
    call_type: CallType
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    risk_score: float = 0.0
    stage: Optional[AttackStage] = None


@dataclass
class CallGraph:
    """Graph representation of MCP session"""
    session_id: str
    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    start_time: datetime = field(default_factory=datetime.now)
    call_count: int = 0
    
    def add_call(self, call_node: MCPCallNode):
        """Add a call to the graph"""
        self.graph.add_node(
            call_node.call_id,
            **call_node.__dict__
        )
        self.call_count += 1
    
    def add_dependency(self, from_call_id: str, to_call_id: str, dep_type: str):
        """Add edge showing dependency between calls"""
        self.graph.add_edge(from_call_id, to_call_id, type=dep_type)


@dataclass
class BehavioralRisk:
    """Risk assessment from behavioral analysis"""
    risk_score: float  # 0.0 to 1.0
    confidence: float
    attack_stages_detected: List[AttackStage]
    suspicious_patterns: List[str]
    call_chains: List[List[str]]
    evidence: List[str]
    graph_features: Dict[str, Any]


class GraphNeuralNetwork(nn.Module):
    """
    NOVEL: Graph Neural Network for attack pattern detection.
    
    Learns to recognize attack patterns in call graphs
    that aren't captured by predefined rules.
    """
    
    def __init__(self, node_feature_dim: int = 64, hidden_dim: int = 128):
        super().__init__()
        
        # Graph convolution layers
        self.conv1 = nn.Linear(node_feature_dim, hidden_dim)
        self.conv2 = nn.Linear(hidden_dim, hidden_dim)
        self.conv3 = nn.Linear(hidden_dim, hidden_dim // 2)
        
        # Classification head
        self.classifier = nn.Linear(hidden_dim // 2, 1)  # Binary: attack or benign
        
        self.dropout = nn.Dropout(0.2)
    
    def forward(self, node_features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through GNN.
        
        Args:
            node_features: [num_nodes, feature_dim]
            adjacency: [num_nodes, num_nodes] adjacency matrix
            
        Returns:
            risk_score: [1] Graph-level risk score
        """
        # Graph convolution layer 1
        x = torch.matmul(adjacency, node_features)
        x = F.relu(self.conv1(x))
        x = self.dropout(x)
        
        # Graph convolution layer 2
        x = torch.matmul(adjacency, x)
        x = F.relu(self.conv2(x))
        x = self.dropout(x)
        
        # Graph convolution layer 3
        x = torch.matmul(adjacency, x)
        x = F.relu(self.conv3(x))
        
        # Global pooling (mean)
        graph_embedding = torch.mean(x, dim=0)
        
        # Classification
        risk_score = torch.sigmoid(self.classifier(graph_embedding))
        
        return risk_score


class CallGraphAnalyzer:
    """
    NOVEL: First graph-based behavioral analyzer for MCP.
    
    Key Innovations:
    1. Models MCP sessions as directed graphs
    2. Detects multi-stage attack patterns
    3. Uses GNN for novel pattern detection
    4. Analyzes temporal and spatial relationships
    
    Attack Detection Examples:
    - list_files → read_multiple_files → send_http (exfiltration chain)
    - read_config → modify_settings → execute_code (privilege escalation)
    - query_db → query_db → query_db (reconnaissance pattern)
    """
    
    def __init__(self):
        self.session_graphs: Dict[str, CallGraph] = {}
        self.attack_patterns = self._load_attack_patterns()
        
        # GNN for novel attack detection
        self.gnn = GraphNeuralNetwork()
        self.gnn.eval()  # Start in eval mode
        
        logger.info("Call Graph Analyzer initialized")
    
    def _load_attack_patterns(self) -> Dict[str, List[List[str]]]:
        """
        Load known multi-stage attack patterns.
        
        These are graph patterns (sequences of tool calls) that
        indicate attacks.
        """
        return {
            "data_exfiltration": [
                ["read_file", "send_http"],
                ["read_file", "write_file", "send_http"],
                ["list_files", "read_multiple", "external_api"],
                ["query_database", "encode_data", "network_request"]
            ],
            "privilege_escalation": [
                ["read_config", "modify_settings", "restart_service"],
                ["list_users", "create_user", "grant_permissions"],
                ["read_credentials", "authenticate", "elevated_action"]
            ],
            "reconnaissance": [
                ["list_files", "list_files", "list_files"],  # Enumeration
                ["query_system", "query_network", "query_processes"],
                ["read_multiple_files", "analyze_structure"]
            ],
            "persistence": [
                ["create_file", "modify_startup", "schedule_task"],
                ["write_config", "create_service", "enable_autostart"]
            ],
            "lateral_movement": [
                ["discover_hosts", "connect_remote", "execute_remote"],
                ["read_credentials", "authenticate_remote", "deploy_agent"]
            ]
        }
    
    def analyze_session(
        self,
        session_id: str,
        calls: Optional[List[Dict[str, Any]]] = None
    ) -> BehavioralRisk:
        """
        Analyze an MCP session's call graph for suspicious behavior.
        
        Args:
            session_id: Session identifier
            calls: Optional list of calls (if not already tracked)
            
        Returns:
            BehavioralRisk with detailed assessment
        """
        logger.info("Analyzing session", session_id=session_id)
        
        # Get or create call graph
        if session_id not in self.session_graphs:
            if not calls:
                logger.warning("No calls provided for new session")
                return self._empty_risk()
            
            self.session_graphs[session_id] = self._build_call_graph(session_id, calls)
        
        call_graph = self.session_graphs[session_id]
        
        # Extract graph features
        features = self.extract_graph_features(call_graph)
        
        # Detect known attack patterns
        matched_patterns = self.match_attack_patterns(call_graph)
        
        # Detect novel patterns with GNN
        gnn_risk = self.detect_novel_patterns(call_graph)
        
        # Identify attack stages
        stages = self.identify_attack_stages(call_graph)
        
        # Extract suspicious call chains
        chains = self.extract_suspicious_chains(call_graph)
        
        # Aggregate risk
        risk = self.aggregate_behavioral_risk(
            features,
            matched_patterns,
            gnn_risk,
            stages,
            chains
        )
        
        logger.info(
            "Session analysis complete",
            session_id=session_id,
            risk_score=risk.risk_score,
            patterns=len(matched_patterns)
        )
        
        return risk
    
    def _build_call_graph(
        self,
        session_id: str,
        calls: List[Dict[str, Any]]
    ) -> CallGraph:
        """
        Build call graph from list of calls.
        
        Creates nodes for each call and edges for dependencies.
        """
        graph = CallGraph(session_id=session_id)
        
        for i, call in enumerate(calls):
            # Create call node
            node = MCPCallNode(
                call_id=f"{session_id}-{i}",
                timestamp=datetime.now(),
                tool=call.get("tool", "unknown"),
                call_type=self._infer_call_type(call.get("tool", "")),
                arguments=call.get("arguments", {}),
                result=call.get("result")
            )
            
            graph.add_call(node)
            
            # Add dependencies based on data flow
            if i > 0:
                prev_call = calls[i - 1]
                if self._has_data_dependency(prev_call, call):
                    graph.add_dependency(
                        f"{session_id}-{i-1}",
                        f"{session_id}-{i}",
                        "data_flow"
                    )
        
        return graph
    
    def _infer_call_type(self, tool: str) -> CallType:
        """Infer call type from tool name"""
        tool_lower = tool.lower()
        
        if any(k in tool_lower for k in ["read", "get", "list", "query"]):
            return CallType.READ
        elif any(k in tool_lower for k in ["write", "create", "delete", "update"]):
            return CallType.WRITE
        elif any(k in tool_lower for k in ["exec", "run", "eval", "execute"]):
            return CallType.EXECUTE
        elif any(k in tool_lower for k in ["http", "network", "api", "send"]):
            return CallType.NETWORK
        elif any(k in tool_lower for k in ["system", "process", "service"]):
            return CallType.SYSTEM
        else:
            return CallType.QUERY
    
    def _has_data_dependency(self, call1: Dict, call2: Dict) -> bool:
        """Check if call2 depends on data from call1"""
        # Simple heuristic: output from call1 appears in call2 arguments
        result1 = str(call1.get("result", ""))
        args2 = str(call2.get("arguments", {}))
        
        # Check if result content appears in next call's arguments
        if result1 and len(result1) > 10 and result1[:20] in args2:
            return True
        
        return False
    
    def extract_graph_features(self, call_graph: CallGraph) -> Dict[str, Any]:
        """
        Extract graph-level features for analysis.
        
        NOVEL: These features capture structural properties
        of the call graph that indicate attacks.
        """
        G = call_graph.graph
        
        features = {
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "density": nx.density(G) if G.number_of_nodes() > 0 else 0,
            "avg_degree": sum(dict(G.degree()).values()) / max(G.number_of_nodes(), 1),
        }
        
        # Path-based features
        if G.number_of_nodes() > 1:
            try:
                features["avg_path_length"] = nx.average_shortest_path_length(G)
            except:
                features["avg_path_length"] = 0
        
        # Call type distribution
        call_types = {}
        for node in G.nodes(data=True):
            call_type = node[1].get("call_type", CallType.QUERY).value
            call_types[call_type] = call_types.get(call_type, 0) + 1
        features["call_type_distribution"] = call_types
        
        # Temporal features
        if G.number_of_nodes() > 0:
            timestamps = [node[1].get("timestamp") for node in G.nodes(data=True)]
            if timestamps and all(timestamps):
                time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                             for i in range(len(timestamps)-1) if i+1 < len(timestamps)]
                features["avg_call_interval"] = sum(time_diffs) / max(len(time_diffs), 1) if time_diffs else 0
        
        return features
    
    def match_attack_patterns(self, call_graph: CallGraph) -> List[Tuple[str, List[str]]]:
        """
        Match known attack patterns in the call graph.
        
        Returns list of (attack_type, matched_chain) tuples.
        """
        G = call_graph.graph
        matched = []
        
        # Get all simple paths up to length 5
        nodes = list(G.nodes())
        
        for attack_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                # Try to find pattern in graph
                for start_node in nodes:
                    if self._pattern_matches(G, start_node, pattern):
                        matched.append((attack_type, pattern))
                        logger.warning(
                            "Attack pattern detected",
                            attack_type=attack_type,
                            pattern=pattern
                        )
        
        return matched
    
    def _pattern_matches(
        self,
        G: nx.DiGraph,
        start_node: str,
        pattern: List[str]
    ) -> bool:
        """Check if pattern matches starting from node"""
        if len(pattern) == 0:
            return True
        
        # Get tool name for start node
        node_data = G.nodes[start_node]
        tool = node_data.get("tool", "").lower()
        
        # Check if first pattern element matches
        if pattern[0].lower() not in tool:
            return False
        
        # Recursively check successors
        if len(pattern) == 1:
            return True
        
        for successor in G.successors(start_node):
            if self._pattern_matches(G, successor, pattern[1:]):
                return True
        
        return False
    
    def detect_novel_patterns(self, call_graph: CallGraph) -> float:
        """
        Use GNN to detect novel attack patterns.
        
        Returns risk score from GNN.
        """
        G = call_graph.graph
        
        if G.number_of_nodes() == 0:
            return 0.0
        
        try:
            # Convert graph to tensors
            node_features, adjacency = self._graph_to_tensors(G)
            
            # Run GNN inference
            with torch.no_grad():
                risk_score = self.gnn(node_features, adjacency)
            
            return risk_score.item()
        except Exception as e:
            logger.warning("GNN inference failed", error=str(e))
            return 0.0
    
    def _graph_to_tensors(self, G: nx.DiGraph) -> Tuple[torch.Tensor, torch.Tensor]:
        """Convert NetworkX graph to PyTorch tensors"""
        num_nodes = G.number_of_nodes()
        
        # Create node feature matrix (simple encoding)
        node_features = torch.zeros(num_nodes, 64)
        for i, (node, data) in enumerate(G.nodes(data=True)):
            # Encode call type
            call_type = data.get("call_type", CallType.QUERY)
            node_features[i, call_type.value.__hash__() % 64] = 1.0
        
        # Create adjacency matrix
        adjacency = torch.zeros(num_nodes, num_nodes)
        node_list = list(G.nodes())
        for i, node1 in enumerate(node_list):
            for j, node2 in enumerate(node_list):
                if G.has_edge(node1, node2):
                    adjacency[i, j] = 1.0
        
        # Add self-loops
        adjacency += torch.eye(num_nodes)
        
        # Normalize
        degree = adjacency.sum(dim=1, keepdim=True)
        adjacency = adjacency / (degree + 1e-6)
        
        return node_features, adjacency
    
    def identify_attack_stages(self, call_graph: CallGraph) -> List[AttackStage]:
        """Identify which attack stages are present"""
        G = call_graph.graph
        stages = set()
        
        for node, data in G.nodes(data=True):
            tool = data.get("tool", "").lower()
            call_type = data.get("call_type")
            
            # Reconnaissance stage
            if call_type == CallType.READ and any(k in tool for k in ["list", "query", "discover"]):
                stages.add(AttackStage.RECONNAISSANCE)
            
            # Exploitation stage
            if call_type in [CallType.WRITE, CallType.EXECUTE]:
                stages.add(AttackStage.EXPLOITATION)
            
            # Exfiltration stage
            if call_type == CallType.NETWORK and any(k in tool for k in ["send", "http", "api"]):
                stages.add(AttackStage.EXFILTRATION)
            
            # Persistence stage
            if any(k in tool for k in ["create", "schedule", "startup", "service"]):
                stages.add(AttackStage.PERSISTENCE)
        
        return list(stages)
    
    def extract_suspicious_chains(self, call_graph: CallGraph) -> List[List[str]]:
        """Extract suspicious call chains"""
        G = call_graph.graph
        chains = []
        
        # Find long chains (potential multi-stage attacks)
        for node in G.nodes():
            # Get all paths from this node
            for target in G.nodes():
                if node != target:
                    try:
                        paths = list(nx.all_simple_paths(G, node, target, cutoff=5))
                        for path in paths:
                            if len(path) >= 3:  # At least 3 steps
                                tool_chain = [G.nodes[n].get("tool") for n in path]
                                chains.append(tool_chain)
                    except:
                        pass
        
        return chains[:10]  # Return top 10
    
    def aggregate_behavioral_risk(
        self,
        features: Dict,
        matched_patterns: List,
        gnn_risk: float,
        stages: List[AttackStage],
        chains: List
    ) -> BehavioralRisk:
        """Aggregate all behavioral signals into final risk"""
        
        # Base risk from matched patterns
        pattern_risk = min(len(matched_patterns) * 0.3, 0.9)
        
        # Risk from attack stages
        stage_risk = len(stages) * 0.15
        
        # Risk from call chains
        chain_risk = min(len(chains) * 0.1, 0.5)
        
        # Aggregate
        risk_score = max(pattern_risk, gnn_risk, stage_risk, chain_risk)
        risk_score = min(risk_score, 1.0)
        
        # Build evidence
        evidence = []
        if matched_patterns:
            evidence.append(f"{len(matched_patterns)} attack patterns matched")
        if stages:
            evidence.append(f"Attack stages detected: {[s.value for s in stages]}")
        if gnn_risk > 0.7:
            evidence.append(f"GNN detected novel pattern (score: {gnn_risk:.2f})")
        if len(chains) > 3:
            evidence.append(f"{len(chains)} suspicious call chains found")
        
        # Confidence based on evidence strength
        confidence = min(len(evidence) * 0.25, 1.0)
        
        return BehavioralRisk(
            risk_score=risk_score,
            confidence=confidence,
            attack_stages_detected=stages,
            suspicious_patterns=[p[0] for p in matched_patterns],
            call_chains=chains[:5],
            evidence=evidence,
            graph_features=features
        )
    
    def _empty_risk(self) -> BehavioralRisk:
        """Return empty risk result"""
        return BehavioralRisk(
            risk_score=0.0,
            confidence=0.0,
            attack_stages_detected=[],
            suspicious_patterns=[],
            call_chains=[],
            evidence=["No session data available"],
            graph_features={}
        )
    
    def add_call_to_session(
        self,
        session_id: str,
        call: Dict[str, Any]
    ):
        """Add a new call to an existing session graph"""
        if session_id not in self.session_graphs:
            self.session_graphs[session_id] = CallGraph(session_id=session_id)
        
        graph = self.session_graphs[session_id]
        
        # Create call node
        node = MCPCallNode(
            call_id=f"{session_id}-{graph.call_count}",
            timestamp=datetime.now(),
            tool=call.get("tool", "unknown"),
            call_type=self._infer_call_type(call.get("tool", "")),
            arguments=call.get("arguments", {}),
            result=call.get("result")
        )
        
        graph.add_call(node)

