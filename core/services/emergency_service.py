from typing import List, Dict, Tuple
import re


class EmergencyService:
    """
    Enhanced Emergency Detection Service for medical chatbot.
    Detects potential medical emergencies and provides appropriate urgency levels.
    """
    
    # Critical emergencies - require immediate 911/emergency services
    CRITICAL_EMERGENCY_KEYWORDS = [
        # Cardiac/Respiratory
        "chest pain", "heart attack", "can't breathe", "cannot breathe",
        "difficulty breathing", "shortness of breath", "choking",
        "severe chest pressure", "crushing chest pain",
        
        # Neurological
        "stroke", "face drooping", "arm weakness", "slurred speech",
        "severe head injury", "loss of consciousness", "unconscious",
        "seizure", "convulsion", "can't wake up",
        
        # Trauma/Bleeding
        "severe bleeding", "heavy bleeding", "bleeding won't stop",
        "major trauma", "severe burn", "deep cut", "stab wound",
        "gunshot", "major accident",
        
        # Allergic/Toxic
        "anaphylaxis", "severe allergic reaction", "throat closing",
        "tongue swelling", "overdose", "poisoning", "swallowed poison",
        
        # Other Critical
        "suicide", "suicidal", "want to die", "kill myself",
        "severe abdominal pain", "coughing blood", "vomiting blood",
        "sudden vision loss", "sudden blindness", "paralysis"
    ]
    
    # High urgency - require immediate medical attention (ER visit within hours)
    HIGH_URGENCY_KEYWORDS = [
        # Pain
        "severe pain", "unbearable pain", "excruciating pain",
        "intense headache", "worst headache",
        
        # Infections/Fever
        "high fever", "fever over 103", "fever with stiff neck",
        "severe infection", "spreading redness",
        
        # Breathing (less severe)
        "trouble breathing", "wheezing badly", "very short of breath",
        
        # Pregnancy-related
        "pregnant and bleeding", "severe pregnancy pain",
        "water broke early", "decreased fetal movement",
        
        # Mental Health
        "self harm", "harming myself", "hurting myself",
        "intrusive thoughts", "severe anxiety attack",
        
        # Other
        "fainting", "fainted", "passed out", "collapsed",
        "severe vomiting", "can't keep anything down",
        "severe diarrhea", "blood in stool", "blood in urine",
        "sudden severe swelling", "eye injury", "chemical in eye"
    ]
    
    # Moderate urgency - should see doctor within 24-48 hours
    MODERATE_URGENCY_KEYWORDS = [
        "persistent fever", "fever for days", "won't go away",
        "ongoing pain", "pain getting worse", "moderate pain",
        "infection", "infected", "pus", "wound not healing",
        "severe cough", "coughing for weeks", "persistent cough",
        "severe rash", "spreading rash", "painful rash",
        "difficulty swallowing", "can't eat", "can't drink",
        "very dizzy", "constant dizziness", "vertigo",
        "dehydrated", "severe dehydration", "not urinating"
    ]
    
    # Context patterns that may reduce urgency (false positives)
    FALSE_POSITIVE_PATTERNS = [
        r"history of",
        r"had .{0,20}(chest pain|seizure|stroke) .{0,20}(years? ago|months? ago|before)",
        r"worried about",
        r"what if",
        r"could i (have|get)",
        r"afraid of",
        r"anxiety about",
        r"read about",
        r"scared of (having|getting)"
    ]
    
    def __init__(self):
        """Initialize the emergency service with compiled regex patterns."""
        self.false_positive_regex = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.FALSE_POSITIVE_PATTERNS
        ]
    
    def is_emergency(self, text: str) -> bool:
        """
        Check if text contains emergency keywords.
        
        Args:
            text: User's message text
            
        Returns:
            bool: True if critical or high urgency emergency detected
        """
        urgency_level, _ = self.assess_urgency(text)
        return urgency_level in ["critical", "high"]
    
    def assess_urgency(self, text: str) -> Tuple[str, List[str]]:
        """
        Assess the urgency level of the medical situation.
        
        Args:
            text: User's message text
            
        Returns:
            Tuple[str, List[str]]: (urgency_level, matched_keywords)
            urgency_level: "critical", "high", "moderate", or "none"
            matched_keywords: List of keywords that were matched
        """
        text_lower = text.lower()
        
        # Check for false positives (past events, hypotheticals)
        if self._is_false_positive(text_lower):
            return "none", []
        
        # Check critical emergencies first
        critical_matches = [
            keyword for keyword in self.CRITICAL_EMERGENCY_KEYWORDS
            if keyword in text_lower
        ]
        if critical_matches:
            return "critical", critical_matches
        
        # Check high urgency
        high_matches = [
            keyword for keyword in self.HIGH_URGENCY_KEYWORDS
            if keyword in text_lower
        ]
        if high_matches:
            return "high", high_matches
        
        # Check moderate urgency
        moderate_matches = [
            keyword for keyword in self.MODERATE_URGENCY_KEYWORDS
            if keyword in text_lower
        ]
        if moderate_matches:
            return "moderate", moderate_matches
        
        return "none", []
    
    def _is_false_positive(self, text: str) -> bool:
        """
        Check if the text contains patterns indicating false positive
        (e.g., past events, hypothetical questions).
        
        Args:
            text: Lowercase user text
            
        Returns:
            bool: True if likely a false positive
        """
        return any(pattern.search(text) for pattern in self.false_positive_regex)
    
    def get_emergency_response(self, text: str) -> Dict[str, any]:
        """
        Get complete emergency assessment with response guidance.
        
        Args:
            text: User's message text
            
        Returns:
            Dict containing:
                - is_emergency (bool)
                - urgency_level (str)
                - matched_keywords (List[str])
                - message (str): Appropriate response message
                - should_show_banner (bool): Whether to show emergency banner
        """
        urgency_level, matched_keywords = self.assess_urgency(text)
        
        response = {
            "is_emergency": urgency_level in ["critical", "high"],
            "urgency_level": urgency_level,
            "matched_keywords": matched_keywords,
            "should_show_banner": False,
            "message": ""
        }
        
        if urgency_level == "critical":
            response["should_show_banner"] = True
            response["message"] = (
                "🚨 **EMERGENCY ALERT** 🚨\n\n"
                "Based on your symptoms, this could be a medical emergency.\n\n"
                "**Please take immediate action:**\n"
                "• Call emergency services (911 in US, 112 in EU, or your local emergency number)\n"
                "• Go to the nearest emergency room immediately\n"
                "• Do not drive yourself - call an ambulance if needed\n\n"
                "If someone is with you, inform them of your symptoms.\n\n"
                "⚠️ While I can provide information, emergency situations require immediate professional medical attention."
            )
        
        elif urgency_level == "high":
            response["should_show_banner"] = True
            response["message"] = (
                "⚠️ **URGENT MEDICAL ATTENTION NEEDED** ⚠️\n\n"
                "Your symptoms suggest you should seek immediate medical care.\n\n"
                "**Recommended actions:**\n"
                "• Visit an emergency room or urgent care center today\n"
                "• Call your doctor immediately\n"
                "• Do not wait to see if symptoms improve\n\n"
                "If symptoms worsen rapidly, call emergency services.\n\n"
                "I can provide general information, but you need professional evaluation."
            )
        
        elif urgency_level == "moderate":
            response["message"] = (
                "⚠️ **Medical Attention Recommended** ⚠️\n\n"
                "Your symptoms suggest you should see a healthcare provider soon.\n\n"
                "**Recommended actions:**\n"
                "• Schedule an appointment with your doctor within 24-48 hours\n"
                "• Monitor your symptoms for any worsening\n"
                "• Visit urgent care if symptoms worsen or you can't get an appointment\n\n"
                "Let me provide some information while you arrange to see a healthcare provider."
            )
        
        return response
    
    def add_emergency_banner(self, response_text: str, urgency_info: Dict) -> str:
        """
        Add emergency banner to chatbot response if needed.
        
        Args:
            response_text: Original chatbot response
            urgency_info: Dict from get_emergency_response()
            
        Returns:
            str: Response with banner prepended if applicable
        """
        if urgency_info["should_show_banner"] and urgency_info["message"]:
            return f"{urgency_info['message']}\n\n---\n\n{response_text}"
        elif urgency_info["message"]:
            return f"{urgency_info['message']}\n\n{response_text}"
        return response_text
    
    @staticmethod
    def get_emergency_resources() -> Dict[str, str]:
        """
        Get emergency contact resources by region.
        
        Returns:
            Dict of region -> emergency numbers
        """
        return {
            "US/Canada": "911",
            "EU": "112",
            "UK": "999 or 112",
            "Australia": "000",
            "India": "102 (ambulance) or 112",
            "Global": "Check local emergency numbers",
            "Suicide Prevention (US)": "988 or 1-800-273-8255",
            "Poison Control (US)": "1-800-222-1222"
        }


# Example usage
if __name__ == "__main__":
    service = EmergencyService()
    
    # Test cases
    test_messages = [
        "I'm having severe chest pain and can't breathe",
        "I had a chest pain last year",
        "What if I have a heart attack?",
        "My fever won't go away",
        "I think I'm having a stroke",
        "Just a mild headache"
    ]
    
    print("Emergency Detection Tests:\n")
    for msg in test_messages:
        result = service.get_emergency_response(msg)
        print(f"Message: {msg}")
        print(f"Urgency: {result['urgency_level']}")
        print(f"Is Emergency: {result['is_emergency']}")
        if result['matched_keywords']:
            print(f"Matched: {result['matched_keywords']}")
        print("-" * 50)