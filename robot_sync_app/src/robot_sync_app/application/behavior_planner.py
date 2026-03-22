from robot_sync_app.domain.models import Utterance, BehaviorPlan


class BehaviorPlanner:
    """Maps text/intent to safe gesture + face expression presets."""
    
    def plan(self, utterance: Utterance) -> BehaviorPlan:
        text = utterance.text.lower()

        if utterance.intent == "arm_calibration":
            return BehaviorPlan(
                speech_text=utterance.text,
                gesture_name="",
                face_expression="EE",
            )

        if "question" in text or utterance.intent == "quiz":
            return BehaviorPlan(
                speech_text=utterance.text,
                gesture_name="fingers_point",
                face_expression="EE",  # Thinking/questioning expression
            )

        if "great" in text or "awesome" in text or "correct" in text:
            return BehaviorPlan(
                speech_text=utterance.text,
                gesture_name="fingers_wave",
                face_expression="Surprise",  # Excited/surprised expression
            )

        return BehaviorPlan(
            speech_text=utterance.text,
            gesture_name="fingers_wave",
            face_expression="Smile",  # Default happy expression
        )
