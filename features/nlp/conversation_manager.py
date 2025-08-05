"""
Conversation Management for Natural Language Processing
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .models import Intent, Entity


class ConversationManager:
    """Handles conversation context and session management"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.context_memory = {}
    
    def apply_context(self, intent: Intent, context: Dict[str, Any], user_input: str) -> Intent:
        """Apply conversation context to refine intent understanding"""
        try:
            # Get conversation data
            previous_intents = context.get("previous_intents", [])
            previous_entities = context.get("previous_entities", [])
            conversation_topic = context.get("topic", None)
            conversation_history = context.get("conversation_history", [])
            
            # Analyze conversation patterns for better context application
            if conversation_history:
                patterns = self._analyze_conversation_patterns(conversation_history)
                session_focus = patterns.get("session_focus", "mixed")
                confidence_trend = patterns.get("confidence_trend", [])
                
                # Adjust confidence based on conversation patterns
                if session_focus == "focused" and len(confidence_trend) > 2:
                    avg_confidence = sum(confidence_trend[-3:]) / 3
                    if avg_confidence > 0.7:
                        intent.confidence = min(intent.confidence + 0.15, 0.95)
                        self.logger.info("Applied context: boosted confidence due to focused conversation")
            
            # Enhanced intent inference for low confidence queries
            if intent.confidence < 0.6 and previous_intents:
                last_intent = previous_intents[-1]
                
                # Progressive conversation patterns
                if any(word in user_input.lower() for word in ["also", "and", "too", "additionally", "plus"]):
                    intent.type = last_intent["type"]
                    intent.confidence = min(intent.confidence + 0.3, 0.9)
                    self.logger.info(f"Applied context: inherited intent type {intent.type} for additive query")
                
                # Refinement patterns
                elif any(word in user_input.lower() for word in ["but", "however", "instead", "rather"]):
                    intent.type = last_intent["type"]
                    intent.confidence = min(intent.confidence + 0.25, 0.85)
                    self.logger.info(f"Applied context: inherited intent type {intent.type} for refinement query")
            
            # Smart target data merging based on conversation flow
            if conversation_topic and conversation_topic in user_input.lower():
                # Get most relevant previous targets
                recent_targets = []
                for prev_intent in previous_intents[-3:]:  # Last 3 intents
                    if prev_intent.get("target_data"):
                        recent_targets.extend(prev_intent["target_data"])
                
                # Add targets that appear frequently in recent conversation
                if recent_targets:
                    target_frequency = {}
                    for target in recent_targets:
                        target_frequency[target] = target_frequency.get(target, 0) + 1
                    
                    # Add frequent targets to current intent
                    for target, freq in target_frequency.items():
                        if freq >= 2 and target not in intent.target_data:
                            intent.target_data.append(target)
                    
                    if target_frequency:
                        self.logger.info(f"Applied context: merged frequent targets from conversation")
            
            # Enhanced filter inheritance with smart merging
            if intent.confidence < 0.7 and previous_intents:
                for prev_intent in reversed(previous_intents[-2:]):  # Check last 2 intents
                    if prev_intent.get("filters") and len(prev_intent["filters"]) > 0:
                        # Merge compatible filters
                        for filter_key, filter_value in prev_intent["filters"].items():
                            if filter_key not in intent.filters:
                                intent.filters[filter_key] = filter_value
                        
                        intent.confidence = min(intent.confidence + 0.2, 0.9)
                        self.logger.info(f"Applied context: inherited {len(prev_intent['filters'])} filters")
                        break
            
            # Context-aware entity enhancement
            if previous_entities and len(previous_entities) > 0:
                # Look for entity patterns that might be relevant
                recent_entity_types = [entity["type"] for entity in previous_entities[-5:]]
                current_entity_types = [entity.type for entity in []]  # Would need entities parameter
                
                # If user has been consistently using certain entity types
                for entity_type in set(recent_entity_types):
                    if recent_entity_types.count(entity_type) >= 2:
                        # Suggest they might want similar criteria
                        intent.conditions.append("consider_previous_criteria")
                        self.logger.info("Applied context: flagged to consider previous criteria")
            
            # Temporal context awareness
            if conversation_history:
                last_interaction = conversation_history[-1]
                time_since_last = datetime.now() - datetime.fromisoformat(last_interaction["timestamp"])
                
                # If it's been a while, reduce context influence
                if time_since_last.total_seconds() > 3600:  # 1 hour
                    intent.confidence = max(intent.confidence - 0.1, 0.1)
                    self.logger.info("Applied context: reduced confidence due to time gap")
                # If very recent, boost confidence
                elif time_since_last.total_seconds() < 60:  # 1 minute
                    intent.confidence = min(intent.confidence + 0.1, 0.95)
                    self.logger.info("Applied context: boosted confidence due to immediate follow-up")
            
            return intent
            
        except Exception as e:
            self.logger.error(f"Error applying context: {e}")
            return intent
    
    def update_context_memory(self, session_id: str, user_input: str, intent: Intent, entities: List[Entity]) -> None:
        """Update conversation context memory for session"""
        try:
            if session_id not in self.context_memory:
                self.context_memory[session_id] = {
                    "previous_intents": [],
                    "previous_entities": [],
                    "conversation_history": [],
                    "topic": None,
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
            
            context = self.context_memory[session_id]
            
            # Add current interaction to history
            context["conversation_history"].append({
                "user_input": user_input,
                "intent": {
                    "type": intent.type,
                    "confidence": intent.confidence,
                    "target_data": intent.target_data,
                    "filters": intent.filters,
                    "conditions": intent.conditions
                },
                "entities": [
                    {
                        "type": entity.type,
                        "value": entity.value,
                        "confidence": entity.confidence,
                        "context": entity.context
                    } for entity in entities
                ],
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only last 10 interactions to prevent memory bloat
            if len(context["conversation_history"]) > 10:
                context["conversation_history"] = context["conversation_history"][-10:]
            
            # Update previous intents (keep last 5)
            context["previous_intents"].append({
                "type": intent.type,
                "confidence": intent.confidence,
                "target_data": intent.target_data,
                "filters": intent.filters,
                "conditions": intent.conditions,
                "timestamp": datetime.now().isoformat()
            })
            if len(context["previous_intents"]) > 5:
                context["previous_intents"] = context["previous_intents"][-5:]
            
            # Update previous entities (keep last 20)
            for entity in entities:
                context["previous_entities"].append({
                    "type": entity.type,
                    "value": entity.value,
                    "confidence": entity.confidence,
                    "context": entity.context,
                    "timestamp": datetime.now().isoformat()
                })
            if len(context["previous_entities"]) > 20:
                context["previous_entities"] = context["previous_entities"][-20:]
            
            # Detect conversation topic from target data
            if intent.target_data:
                most_common_target = max(set(intent.target_data), key=intent.target_data.count)
                context["topic"] = most_common_target
            
            # Update timestamp
            context["last_updated"] = datetime.now().isoformat()
            
            self.logger.info(f"Updated context memory for session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating context memory: {e}")
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation for a session"""
        try:
            if session_id not in self.context_memory:
                return {
                    "session_exists": False,
                    "message": "No conversation history found for this session"
                }
            
            context = self.context_memory[session_id]
            history = context.get("conversation_history", [])
            
            if not history:
                return {
                    "session_exists": True,
                    "conversation_count": 0,
                    "message": "No conversation history available"
                }
            
            # Analyze conversation patterns
            intent_types = [item["intent"]["type"] for item in history]
            most_common_intent = max(set(intent_types), key=intent_types.count) if intent_types else None
            
            # Get most common targets
            all_targets = []
            for item in history:
                all_targets.extend(item["intent"]["target_data"])
            
            target_counts = {}
            for target in all_targets:
                target_counts[target] = target_counts.get(target, 0) + 1
            
            most_common_targets = sorted(target_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Get recent queries
            recent_queries = [item["user_input"] for item in history[-3:]]
            
            return {
                "session_exists": True,
                "session_id": session_id,
                "conversation_count": len(history),
                "created_at": context.get("created_at"),
                "last_updated": context.get("last_updated"),
                "current_topic": context.get("topic"),
                "most_common_intent": most_common_intent,
                "most_common_targets": [{"target": target, "count": count} for target, count in most_common_targets],
                "recent_queries": recent_queries,
                "total_entities_extracted": len(context.get("previous_entities", [])),
                "conversation_patterns": self._analyze_conversation_patterns(history)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting conversation summary: {e}")
            return {
                "session_exists": False,
                "error": str(e),
                "message": "Error retrieving conversation summary"
            }
    
    def _analyze_conversation_patterns(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in conversation history"""
        try:
            patterns = {
                "confidence_trend": [],
                "common_filters": {},
                "session_focus": "mixed",
                "learning_indicators": []
            }
            
            # Analyze confidence trend
            for item in history:
                patterns["confidence_trend"].append(item["intent"]["confidence"])
            
            # Analyze common filters
            for item in history:
                for filter_key, filter_value in item["intent"]["filters"].items():
                    if filter_key not in patterns["common_filters"]:
                        patterns["common_filters"][filter_key] = []
                    patterns["common_filters"][filter_key].append(filter_value)
            
            # Determine session focus
            intent_types = [item["intent"]["type"] for item in history]
            if len(set(intent_types)) == 1:
                patterns["session_focus"] = "focused"
            elif len(history) > 3 and len(set(intent_types[-3:])) == 1:
                patterns["session_focus"] = "converging"
            else:
                patterns["session_focus"] = "exploratory"
            
            # Detect learning indicators
            if len(patterns["confidence_trend"]) > 3:
                recent_trend = patterns["confidence_trend"][-3:]
                if all(recent_trend[i] <= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                    patterns["learning_indicators"].append("improving_confidence")
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing conversation patterns: {e}")
            return {"error": str(e)}
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """Clean up old conversation sessions to prevent memory bloat"""
        try:
            current_time = datetime.now()
            sessions_cleaned = 0
            sessions_kept = 0
            
            sessions_to_remove = []
            
            for session_id, context in self.context_memory.items():
                last_updated_str = context.get("last_updated")
                if last_updated_str:
                    try:
                        last_updated = datetime.fromisoformat(last_updated_str)
                        age_hours = (current_time - last_updated).total_seconds() / 3600
                        
                        if age_hours > max_age_hours:
                            sessions_to_remove.append(session_id)
                        else:
                            sessions_kept += 1
                    except ValueError:
                        # Invalid timestamp, remove session
                        sessions_to_remove.append(session_id)
                else:
                    # No timestamp, remove session
                    sessions_to_remove.append(session_id)
            
            # Remove old sessions
            for session_id in sessions_to_remove:
                del self.context_memory[session_id]
                sessions_cleaned += 1
            
            self.logger.info(f"Session cleanup: removed {sessions_cleaned}, kept {sessions_kept}")
            
            return {
                "sessions_cleaned": sessions_cleaned,
                "sessions_kept": sessions_kept,
                "cleanup_timestamp": current_time.isoformat(),
                "max_age_hours": max_age_hours
            }
            
        except Exception as e:
            self.logger.error(f"Error during session cleanup: {e}")
            return {"error": str(e), "sessions_cleaned": 0, "sessions_kept": 0}
