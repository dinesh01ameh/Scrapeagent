"""
Complex Logic Processing for Natural Language Processing
"""

import re
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from .models import Intent, Entity


class ComplexLogicProcessor:
    """Handles complex conditional logic and multi-step processing"""
    
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
        self.logger = logging.getLogger(__name__)
    
    async def parse_complex_conditions(self, user_input: str, intent: Intent) -> Dict[str, Any]:
        """Parse complex conditional logic from user input"""
        try:
            conditions = {
                "has_complex_logic": False,
                "conditional_statements": [],
                "fallback_actions": [],
                "multi_step_actions": [],
                "complexity_score": 0.0,
                "execution_order": []
            }
            
            user_lower = user_input.lower()
            
            # Detect conditional keywords
            conditional_keywords = ["if", "when", "unless", "in case", "should", "otherwise", "else", "then"]
            conditional_found = any(keyword in user_lower for keyword in conditional_keywords)
            
            if conditional_found:
                conditions["has_complex_logic"] = True
                conditions["complexity_score"] += 0.3
                
                # Parse conditional statements using LLM
                conditional_analysis = await self._analyze_conditionals_with_llm(user_input)
                if conditional_analysis:
                    conditions.update(conditional_analysis)
                    conditions["complexity_score"] += 0.4
            
            # Detect multi-step actions
            multi_step_indicators = ["first", "then", "next", "after", "finally", "also", "and then"]
            if any(indicator in user_lower for indicator in multi_step_indicators):
                conditions["has_complex_logic"] = True
                conditions["complexity_score"] += 0.2
                
                # Parse multi-step sequence
                steps = self._parse_multi_step_sequence(user_input)
                conditions["multi_step_actions"] = steps
                conditions["execution_order"] = [step["order"] for step in steps]
            
            # Detect fallback scenarios
            fallback_indicators = ["if not", "if missing", "if unavailable", "otherwise", "as backup"]
            if any(indicator in user_lower for indicator in fallback_indicators):
                conditions["has_complex_logic"] = True
                conditions["complexity_score"] += 0.3
                
                fallbacks = self._parse_fallback_actions(user_input)
                conditions["fallback_actions"] = fallbacks
            
            # Detect comparison operations
            comparison_indicators = ["compare", "versus", "vs", "against", "difference", "similar to"]
            if any(indicator in user_lower for indicator in comparison_indicators):
                conditions["has_complex_logic"] = True
                conditions["complexity_score"] += 0.2
                conditions["requires_comparison"] = True
            
            # Normalize complexity score
            conditions["complexity_score"] = min(conditions["complexity_score"], 1.0)
            
            self.logger.info(f"Complex logic analysis: score={conditions['complexity_score']:.2f}, has_logic={conditions['has_complex_logic']}")
            
            return conditions
            
        except Exception as e:
            self.logger.error(f"Error parsing complex conditions: {e}")
            return {"has_complex_logic": False, "complexity_score": 0.0, "error": str(e)}
    
    async def _analyze_conditionals_with_llm(self, user_input: str) -> Dict[str, Any]:
        """Use LLM to analyze complex conditional statements"""
        try:
            prompt = f"""
            Analyze this web scraping request for conditional logic:
            
            User Request: "{user_input}"
            
            Identify:
            1. Conditional statements (if/when/unless conditions)
            2. Primary actions and fallback actions
            3. Dependencies between actions
            4. Execution order
            
            Return JSON with this structure:
            {{
                "conditional_statements": [
                    {{
                        "condition": "if price is not visible",
                        "primary_action": "check product detail page",
                        "fallback_action": "mark as unavailable",
                        "confidence": 0.9
                    }}
                ],
                "execution_flow": [
                    {{"step": 1, "action": "extract products", "condition": null}},
                    {{"step": 2, "action": "check prices", "condition": "if price visible"}},
                    {{"step": 3, "action": "check detail page", "condition": "if price not visible"}}
                ]
            }}
            """
            
            response = await self.llm_manager.process_content(
                prompt,
                "conditional_analysis",
                temperature=0.1,
                max_tokens=800
            )
            
            result = json.loads(response)
            return result
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse LLM conditional analysis: {e}")
            return {}
    
    def _parse_multi_step_sequence(self, user_input: str) -> List[Dict[str, Any]]:
        """Parse multi-step action sequences"""
        steps = []
        user_lower = user_input.lower()
        
        # Common step indicators and their patterns
        step_patterns = [
            (r"first,?\s+(.+?)(?:\s+then|\s+next|\s+after|$)", 1),
            (r"then,?\s+(.+?)(?:\s+then|\s+next|\s+after|\s+finally|$)", 2),
            (r"next,?\s+(.+?)(?:\s+then|\s+next|\s+after|\s+finally|$)", 3),
            (r"after\s+that,?\s+(.+?)(?:\s+then|\s+next|\s+finally|$)", 4),
            (r"finally,?\s+(.+?)$", 5)
        ]
        
        for pattern, order in step_patterns:
            matches = re.finditer(pattern, user_lower, re.IGNORECASE)
            for match in matches:
                action_text = match.group(1).strip()
                if action_text:
                    steps.append({
                        "order": order,
                        "action": action_text,
                        "type": self._classify_action_type(action_text),
                        "confidence": 0.8
                    })
        
        # Sort by order
        steps.sort(key=lambda x: x["order"])
        return steps
    
    def _parse_fallback_actions(self, user_input: str) -> List[Dict[str, Any]]:
        """Parse fallback action scenarios"""
        fallbacks = []
        user_lower = user_input.lower()
        
        # Fallback patterns
        fallback_patterns = [
            r"if\s+(.+?)\s+(?:is\s+)?(?:not|missing|unavailable),?\s+(.+?)(?:\.|$)",
            r"if\s+(?:you\s+)?(?:can't|cannot)\s+(.+?),?\s+(.+?)(?:\.|$)",
            r"otherwise,?\s+(.+?)(?:\.|$)",
            r"as\s+(?:a\s+)?backup,?\s+(.+?)(?:\.|$)"
        ]
        
        for pattern in fallback_patterns:
            matches = re.finditer(pattern, user_lower, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    condition = match.group(1).strip()
                    action = match.group(2).strip()
                    fallbacks.append({
                        "condition": condition,
                        "fallback_action": action,
                        "type": "conditional_fallback",
                        "confidence": 0.7
                    })
                elif len(match.groups()) == 1:
                    action = match.group(1).strip()
                    fallbacks.append({
                        "condition": "default",
                        "fallback_action": action,
                        "type": "default_fallback",
                        "confidence": 0.6
                    })
        
        return fallbacks
    
    def _classify_action_type(self, action_text: str) -> str:
        """Classify the type of action based on text"""
        action_lower = action_text.lower()
        
        if any(word in action_lower for word in ["extract", "get", "scrape", "collect"]):
            return "extraction"
        elif any(word in action_lower for word in ["filter", "select", "choose", "pick"]):
            return "filtering"
        elif any(word in action_lower for word in ["check", "verify", "validate", "confirm"]):
            return "validation"
        elif any(word in action_lower for word in ["navigate", "go to", "visit", "open"]):
            return "navigation"
        elif any(word in action_lower for word in ["analyze", "process", "understand", "classify"]):
            return "analysis"
        else:
            return "general"
    
    async def build_complex_extraction_config(self, intent: Intent, entities: List[Entity], conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Build extraction config with complex conditional logic and multi-step strategies"""
        try:
            config = {
                "execution_mode": "complex",
                "primary_strategy": self._determine_primary_strategy(intent, entities),
                "conditional_logic": conditions.get("conditional_statements", []),
                "multi_step_actions": conditions.get("multi_step_actions", []),
                "fallback_strategies": conditions.get("fallback_actions", []),
                "execution_metadata": {
                    "complexity_score": conditions.get("complexity_score", 0.0),
                    "requires_llm": True,
                    "estimated_execution_time": self._estimate_execution_time(conditions),
                    "risk_level": self._assess_risk_level(conditions)
                }
            }
            
            # Build execution plan
            execution_plan = []
            
            # Add multi-step actions if present
            if conditions.get("multi_step_actions"):
                for step in conditions["multi_step_actions"]:
                    execution_plan.append({
                        "step_id": f"step_{step['order']}",
                        "action_type": step["type"],
                        "description": step["action"],
                        "strategy": self._determine_strategy_for_action(step["action"]),
                        "dependencies": [],
                        "fallbacks": []
                    })
            
            # Add conditional logic to execution plan
            if conditions.get("conditional_statements"):
                for i, conditional in enumerate(conditions["conditional_statements"]):
                    execution_plan.append({
                        "step_id": f"conditional_{i+1}",
                        "action_type": "conditional",
                        "condition": conditional["condition"],
                        "primary_action": conditional["primary_action"],
                        "fallback_action": conditional.get("fallback_action"),
                        "strategy": "conditional_execution"
                    })
            
            # Add fallback strategies
            if conditions.get("fallback_actions"):
                for i, fallback in enumerate(conditions["fallback_actions"]):
                    execution_plan.append({
                        "step_id": f"fallback_{i+1}",
                        "action_type": "fallback",
                        "condition": fallback["condition"],
                        "action": fallback["fallback_action"],
                        "strategy": "fallback_execution"
                    })
            
            config["execution_plan"] = execution_plan
            
            # Add target data and filters from intent
            config["target_data"] = intent.target_data
            config["filters"] = intent.filters
            config["output_format"] = intent.output_format
            
            # Add entity-based configurations
            for entity in entities:
                if entity.type.value == "price":
                    config.setdefault("price_filters", []).append(entity.value)
                elif entity.type.value == "rating":
                    config.setdefault("rating_filters", []).append(entity.value)
                elif entity.type.value == "date":
                    config.setdefault("date_filters", []).append(entity.value)
            
            self.logger.info(f"Built complex extraction config with {len(execution_plan)} execution steps")
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error building complex extraction config: {e}")
            # Fallback to simple config
            return {
                "execution_mode": "simple",
                "strategy": "css_selector",
                "target_data": intent.target_data,
                "filters": intent.filters,
                "error": str(e)
            }
    
    def _determine_primary_strategy(self, intent: Intent, entities: List[Entity]) -> str:
        """Determine the primary extraction strategy based on intent and entities"""
        if any(entity.type.value in ["price", "rating"] for entity in entities):
            return "structured_data_extraction"
        elif intent.type.value == "analyze_content":
            return "llm_analysis"
        elif len(intent.target_data) > 3:
            return "comprehensive_extraction"
        else:
            return "targeted_extraction"
    
    def _determine_strategy_for_action(self, action: str) -> str:
        """Determine the best extraction strategy for a given action"""
        action_lower = action.lower()
        
        if any(word in action_lower for word in ["navigate", "go to", "click"]):
            return "browser_automation"
        elif any(word in action_lower for word in ["analyze", "understand"]):
            return "llm_analysis"
        elif any(word in action_lower for word in ["extract", "get", "scrape"]):
            return "css_selector"
        else:
            return "auto"
    
    def _estimate_execution_time(self, conditions: Dict[str, Any]) -> int:
        """Estimate execution time based on complexity"""
        base_time = 5  # seconds
        
        # Add time for each complex condition
        complexity_score = conditions.get("complexity_score", 0.0)
        additional_time = int(complexity_score * 10)
        
        # Add time for multi-step actions
        multi_step_count = len(conditions.get("multi_step_actions", []))
        additional_time += multi_step_count * 3
        
        # Add time for conditional statements
        conditional_count = len(conditions.get("conditional_statements", []))
        additional_time += conditional_count * 2
        
        return base_time + additional_time
    
    def _assess_risk_level(self, conditions: Dict[str, Any]) -> str:
        """Assess the risk level of the complex extraction"""
        complexity_score = conditions.get("complexity_score", 0.0)
        
        if complexity_score < 0.3:
            return "low"
        elif complexity_score < 0.7:
            return "medium"
        else:
            return "high"
