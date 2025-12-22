"""
Adaptive Policy Engine (Priority 4 - LOW)

Research-Backed Enhancement: Addresses the limitation that "predefined rule types lack
adaptability to dynamic task scenarios" (DRIFT research, 2025).

Provides context-aware, dynamic risk adjustment based on:
1. User role and trust level
2. Historical behavior patterns  
3. Task context and intent
4. Environmental factors
5. Time-based patterns

Research Foundation:
- DRIFT (Li et al., 2025): Dynamic rule adaptation reduces false positives by 40%
- Research shows static rules cause overblocking in legitimate scenarios
- Adaptive policies balance security with usability

Example Adaptations:
    Static: read_file("../parent") → BLOCK (always)
    
    Adaptive:
    - Developer in code review session → ALLOW (legitimate)
    - Unknown user, suspicious session → BLOCK (attack)
    - Trusted CI/CD pipeline → ALLOW (automation)

Author: Saurabh Yergattikar
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class UserRole(Enum):
    """User roles with different trust levels"""
    UNKNOWN = "unknown"  # Default, untrusted
    USER = "user"  # Standard user
    DEVELOPER = "developer"  # Developer access
    ADMIN = "admin"  # Administrative access
    SERVICE = "service"  # Service account/CI-CD
    TRUSTED_SERVICE = "trusted_service"  # Verified automation


class TaskContext(Enum):
    """Context/intent of current task"""
    UNKNOWN = "unknown"
    FILE_OPERATION = "file_operation"
    CODE_REVIEW = "code_review"
    DATA_ANALYSIS = "data_analysis"
    API_INTEGRATION = "api_integration"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    DEBUGGING = "debugging"


class TrustLevel(Enum):
    """User trust level based on history"""
    UNTRUSTED = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERIFIED = 4


@dataclass
class UserProfile:
    """Profile tracking user behavior and trust"""
    user_id: str
    role: UserRole
    trust_level: TrustLevel
    total_calls: int = 0
    blocked_calls: int = 0
    false_positive_reports: int = 0
    last_seen: datetime = field(default_factory=datetime.now)
    first_seen: datetime = field(default_factory=datetime.now)
    typical_tools: List[str] = field(default_factory=list)
    typical_times: List[int] = field(default_factory=list)  # Hours of day


@dataclass
class SessionContext:
    """Context for current session"""
    session_id: str
    user_id: str
    task_context: TaskContext
    start_time: datetime
    call_count: int = 0
    tools_used: List[str] = field(default_factory=list)
    risk_events: int = 0


@dataclass
class AdaptiveDecision:
    """Decision with adaptive adjustment"""
    original_risk: float
    adjusted_risk: float
    adjustment_factor: float
    adjustments_applied: List[str]
    allow: bool
    reason: str


class AdaptivePolicyEngine:
    """
    LOW PRIORITY ENHANCEMENT (Priority 4)
    
    Dynamically adjusts security policies based on context.
    
    Key Innovations:
    1. User behavior profiling (learn normal patterns)
    2. Context-aware risk adjustment (task intent matters)
    3. Time-based adaptation (legitimate times vs suspicious)
    4. False positive feedback loop (learn from mistakes)
    
    Research Validation:
    - DRIFT: Dynamic adaptation reduced false positives by 40%
    - Static rules: 15-20% false positive rate
    - Adaptive rules: 5-10% false positive rate
    
    How It Works:
    
    Base Detection:
        read_file("../config.json") → Risk: 0.75 (HIGH)
    
    Context Adjustments:
        + User is Developer → -0.20 (trusted role)
        + Task is Code Review → -0.15 (legitimate context)
        + Time is business hours → -0.05 (normal time)
        + User has clean history → -0.10 (trust bonus)
        
        Adjusted Risk: 0.75 - 0.50 = 0.25 (LOW) → ALLOW
    
    Without Adaptive:
        Would BLOCK (false positive, frustrates developers)
    
    With Adaptive:
        Allows legitimate use, still blocks actual attacks
    
    Usage:
        engine = AdaptivePolicyEngine()
        
        # Register user
        engine.register_user("user123", UserRole.DEVELOPER)
        
        # Make decision
        decision = engine.adapt_decision(
            user_id="user123",
            session_context=context,
            base_risk=0.75,
            call=mcp_call
        )
        
        if decision.allow:
            return ALLOW
    """
    
    def __init__(self):
        """Initialize adaptive policy engine"""
        self.user_profiles: Dict[str, UserProfile] = {}
        self.session_contexts: Dict[str, SessionContext] = {}
        self.global_stats = {
            "total_decisions": 0,
            "adaptations_applied": 0,
            "false_positives_prevented": 0
        }
        
        logger.info("Adaptive Policy Engine initialized")
    
    def register_user(
        self,
        user_id: str,
        role: UserRole = UserRole.USER,
        trust_level: Optional[TrustLevel] = None
    ):
        """Register or update a user"""
        if user_id not in self.user_profiles:
            # New user
            if trust_level is None:
                # Assign initial trust based on role
                trust_map = {
                    UserRole.UNKNOWN: TrustLevel.UNTRUSTED,
                    UserRole.USER: TrustLevel.LOW,
                    UserRole.DEVELOPER: TrustLevel.MEDIUM,
                    UserRole.ADMIN: TrustLevel.HIGH,
                    UserRole.SERVICE: TrustLevel.MEDIUM,
                    UserRole.TRUSTED_SERVICE: TrustLevel.VERIFIED
                }
                trust_level = trust_map.get(role, TrustLevel.LOW)
            
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                role=role,
                trust_level=trust_level
            )
            
            logger.info(
                "Registered new user",
                user_id=user_id,
                role=role.value,
                trust=trust_level.value
            )
        else:
            # Update existing
            profile = self.user_profiles[user_id]
            profile.role = role
            if trust_level:
                profile.trust_level = trust_level
    
    def create_session_context(
        self,
        session_id: str,
        user_id: str,
        task_context: TaskContext = TaskContext.UNKNOWN
    ) -> SessionContext:
        """Create new session context"""
        context = SessionContext(
            session_id=session_id,
            user_id=user_id,
            task_context=task_context,
            start_time=datetime.now()
        )
        
        self.session_contexts[session_id] = context
        return context
    
    def adapt_decision(
        self,
        user_id: str,
        session_id: str,
        base_risk: float,
        call: Dict[str, Any]
    ) -> AdaptiveDecision:
        """
        Adapt security decision based on context.
        
        This is the main decision point.
        
        Args:
            user_id: User making the call
            session_id: Current session
            base_risk: Risk score from 4-channel detection
            call: The MCP call being evaluated
            
        Returns:
            AdaptiveDecision with adjusted risk and allow/block decision
        """
        self.global_stats["total_decisions"] += 1
        
        # Get user profile (create if doesn't exist)
        if user_id not in self.user_profiles:
            self.register_user(user_id, UserRole.USER)
        
        profile = self.user_profiles[user_id]
        
        # Get session context
        context = self.session_contexts.get(session_id)
        if not context:
            context = self.create_session_context(session_id, user_id)
        
        # Apply adjustments
        adjustments = []
        total_adjustment = 0.0
        
        # 1. Role-based adjustment
        role_adj = self._get_role_adjustment(profile.role, call)
        if role_adj != 0:
            total_adjustment += role_adj
            adjustments.append(f"role:{profile.role.value}:{role_adj:+.2f}")
        
        # 2. Trust level adjustment
        trust_adj = self._get_trust_adjustment(profile.trust_level, base_risk)
        if trust_adj != 0:
            total_adjustment += trust_adj
            adjustments.append(f"trust:{profile.trust_level.value}:{trust_adj:+.2f}")
        
        # 3. Task context adjustment
        task_adj = self._get_task_context_adjustment(context.task_context, call)
        if task_adj != 0:
            total_adjustment += task_adj
            adjustments.append(f"task:{context.task_context.value}:{task_adj:+.2f}")
        
        # 4. Behavioral pattern adjustment
        behavior_adj = self._get_behavioral_adjustment(profile, call)
        if behavior_adj != 0:
            total_adjustment += behavior_adj
            adjustments.append(f"behavior:{behavior_adj:+.2f}")
        
        # 5. Temporal adjustment
        temporal_adj = self._get_temporal_adjustment(profile, datetime.now())
        if temporal_adj != 0:
            total_adjustment += temporal_adj
            adjustments.append(f"temporal:{temporal_adj:+.2f}")
        
        # Calculate adjusted risk
        adjusted_risk = max(0.0, min(1.0, base_risk + total_adjustment))
        
        # Decision threshold: 0.70
        allow = adjusted_risk < 0.70
        
        # Build reason
        if adjustments:
            self.global_stats["adaptations_applied"] += 1
            reason_parts = [f"Base risk: {base_risk:.2f}"]
            reason_parts.extend(adjustments)
            reason_parts.append(f"Adjusted: {adjusted_risk:.2f}")
            reason = " | ".join(reason_parts)
        else:
            reason = f"No adjustments (base: {base_risk:.2f})"
        
        # Track if this prevented a false positive
        if not allow and base_risk >= 0.70 and adjusted_risk < 0.70:
            # Adaptation changed BLOCK to ALLOW
            self.global_stats["false_positives_prevented"] += 1
        
        # Update profile
        profile.total_calls += 1
        profile.last_seen = datetime.now()
        
        # Update session
        context.call_count += 1
        tool = call.get("tool", "unknown")
        if tool not in context.tools_used:
            context.tools_used.append(tool)
        
        logger.info(
            "Adaptive decision made",
            user_id=user_id,
            base_risk=base_risk,
            adjusted_risk=adjusted_risk,
            allow=allow,
            adjustments_count=len(adjustments)
        )
        
        return AdaptiveDecision(
            original_risk=base_risk,
            adjusted_risk=adjusted_risk,
            adjustment_factor=total_adjustment,
            adjustments_applied=adjustments,
            allow=allow,
            reason=reason
        )
    
    def _get_role_adjustment(self, role: UserRole, call: Dict) -> float:
        """Get risk adjustment based on user role"""
        tool = call.get("tool", "").lower()
        
        # Developers get more leeway with file operations
        if role in [UserRole.DEVELOPER, UserRole.ADMIN]:
            if any(keyword in tool for keyword in ["file", "read", "write", "list"]):
                return -0.15  # Reduce risk
        
        # Service accounts get leeway for automation
        if role in [UserRole.SERVICE, UserRole.TRUSTED_SERVICE]:
            return -0.10  # General reduction for automation
        
        # Unknown users get no adjustment (or penalty)
        if role == UserRole.UNKNOWN:
            return 0.05  # Slight increase in caution
        
        return 0.0
    
    def _get_trust_adjustment(self, trust: TrustLevel, base_risk: float) -> float:
        """Get risk adjustment based on trust level"""
        # Higher trust = more tolerance for risky calls
        trust_adjustments = {
            TrustLevel.UNTRUSTED: 0.10,  # Increase risk
            TrustLevel.LOW: 0.0,
            TrustLevel.MEDIUM: -0.10,
            TrustLevel.HIGH: -0.15,
            TrustLevel.VERIFIED: -0.20
        }
        
        return trust_adjustments.get(trust, 0.0)
    
    def _get_task_context_adjustment(self, task: TaskContext, call: Dict) -> float:
        """Get risk adjustment based on task context"""
        tool = call.get("tool", "").lower()
        
        # Code review context allows more file traversal
        if task == TaskContext.CODE_REVIEW:
            if "read" in tool or "list" in tool:
                return -0.15
        
        # Testing/debugging allows experimental calls
        if task in [TaskContext.TESTING, TaskContext.DEBUGGING]:
            return -0.10
        
        # Deployment/CI-CD allows automation patterns
        if task == TaskContext.DEPLOYMENT:
            if any(keyword in tool for keyword in ["exec", "run", "deploy"]):
                return -0.10
        
        return 0.0
    
    def _get_behavioral_adjustment(self, profile: UserProfile, call: Dict) -> float:
        """Get risk adjustment based on user's typical behavior"""
        tool = call.get("tool", "")
        
        # Check if this tool is typical for this user
        if tool in profile.typical_tools:
            return -0.05  # Familiar tool, slight reduction
        
        # Check user's history
        if profile.total_calls > 100:
            # Established user
            false_positive_rate = profile.false_positive_reports / max(profile.blocked_calls, 1)
            if false_positive_rate > 0.3:  # >30% of blocks were false positives
                return -0.10  # Give more leeway
        
        return 0.0
    
    def _get_temporal_adjustment(self, profile: UserProfile, current_time: datetime) -> float:
        """Get risk adjustment based on time patterns"""
        current_hour = current_time.hour
        
        # Business hours (9 AM - 6 PM) slightly less risky
        if 9 <= current_hour <= 18:
            return -0.05
        
        # Late night (11 PM - 5 AM) slightly more suspicious
        if current_hour >= 23 or current_hour <= 5:
            return 0.05
        
        # Check if this is typical time for user
        if current_hour in profile.typical_times:
            return -0.03  # User's normal working hours
        
        return 0.0
    
    def report_false_positive(self, user_id: str, call: Dict):
        """User reports a false positive block"""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            profile.false_positive_reports += 1
            
            # Increase trust slightly
            if profile.false_positive_reports > 3 and profile.trust_level.value < TrustLevel.HIGH.value:
                old_trust = profile.trust_level
                profile.trust_level = TrustLevel(min(profile.trust_level.value + 1, TrustLevel.HIGH.value))
                
                logger.info(
                    "Increased user trust level due to false positive reports",
                    user_id=user_id,
                    old_trust=old_trust.name,
                    new_trust=profile.trust_level.name
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adaptive engine statistics"""
        return {
            "total_decisions": self.global_stats["total_decisions"],
            "adaptations_applied": self.global_stats["adaptations_applied"],
            "false_positives_prevented": self.global_stats["false_positives_prevented"],
            "adaptation_rate": self.global_stats["adaptations_applied"] / max(self.global_stats["total_decisions"], 1),
            "total_users": len(self.user_profiles),
            "active_sessions": len(self.session_contexts)
        }


# Singleton instance
_adaptive_engine_instance = None


def get_adaptive_engine() -> AdaptivePolicyEngine:
    """Get singleton adaptive engine instance"""
    global _adaptive_engine_instance
    if _adaptive_engine_instance is None:
        _adaptive_engine_instance = AdaptivePolicyEngine()
    return _adaptive_engine_instance

