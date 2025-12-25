import json
import uuid

from prompts.medical_prompt import build_medical_prompt

class ChatService:
    def __init__(
        self,
        llm,
        emergency,
        context_service,
        followup,
        compliance,
        chat_history
    ):
        self.llm = llm
        self.emergency = emergency
        self.context_service = context_service
        self.followup = followup
        self.compliance = compliance
        self.chat_history = chat_history

    async def analyze(self, firebase_uid: str, symptoms: str):
        """
        Main chat analysis pipeline.
        """

        # Generate a session ID (per chat screen)
        session_id = str(uuid.uuid4())

        # ---------------------------------
        # Save user message
        # ---------------------------------
        await self.chat_history.save_message(
            firebase_uid=firebase_uid,
            session_id=session_id,
            role="user",
            content=symptoms
        )

        # ---------------------------------
        # Emergency override
        # ---------------------------------
        if self.emergency.is_emergency(symptoms):
            emergency_response = {
                "acknowledgement": "Your symptoms may require urgent medical attention.",
                "possible_conditions": ["Potential medical emergency"],
                "suggested_otc_medications": [],
                "precautions": ["Avoid exertion"],
                "when_to_see_doctor": ["Go to emergency immediately"],
                "severity_level": "high",
                "medication_warning": "Do not self-medicate.",
                "follow_up_questions": [],
                "disclaimer": self.compliance.disclaimer()
            }

            # Save assistant message
            await self.chat_history.save_message(
                firebase_uid=firebase_uid,
                session_id=session_id,
                role="assistant",
                content=json.dumps(emergency_response)
            )

            return emergency_response

        # ---------------------------------
        # Build context (from profile later)
        # ---------------------------------
        context_text = await self.context_service.build_context(firebase_uid)

        prompt = build_medical_prompt(
            user_input=symptoms,
            context=context_text
        )

        # ---------------------------------
        # Call Gemini
        # ---------------------------------
        raw = await self.llm.generate(prompt)
        data = json.loads(raw)

        # ---------------------------------
        # Normalize lists
        # ---------------------------------
        for key in [
            "possible_conditions",
            "suggested_otc_medications",
            "precautions",
            "when_to_see_doctor"
        ]:
            data[key] = self.compliance.normalize_list(data.get(key))

        # ---------------------------------
        # Follow-up questions
        # ---------------------------------
        data["follow_up_questions"] = self.followup.generate_questions(
            symptoms,
            data.get("severity_level", "medium")
        )

        # ---------------------------------
        # Disclaimer
        # ---------------------------------
        data["disclaimer"] = self.compliance.disclaimer()

        # ---------------------------------
        # Save assistant message
        # ---------------------------------
        await self.chat_history.save_message(
            firebase_uid=firebase_uid,
            session_id=session_id,
            role="assistant",
            content=json.dumps(data)
        )

        return data