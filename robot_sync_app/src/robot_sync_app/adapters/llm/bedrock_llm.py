import json
import random
import time

import boto3
from botocore.exceptions import ClientError

from robot_sync_app.ports.llm_port import LLMPort


class BedrockLLMAdapter(LLMPort):
    def __init__(self, model_id: str, region: str, system_prompt: str, min_cooldown_sec: float = 1.5) -> None:
        self._model_id = model_id
        self._region = region
        self._system_prompt = system_prompt
        self._min_cooldown_sec = min_cooldown_sec
        self._last_call = 0.0

    def _invoke_with_backoff(self, client: boto3.client, body: str) -> dict:
        base = 0.4
        cap = 8.0
        for attempt in range(10):
            try:
                return client.invoke_model(
                    modelId=self._model_id,
                    body=body,
                    contentType="application/json",
                    accept="application/json",
                )
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "")
                if code in ("ThrottlingException", "TooManyRequestsException"):
                    wait_s = min(cap, base * (2 ** attempt)) * (1 + random.random() * 0.3)
                    print(f"⏳ Bedrock throttled, waiting {wait_s:.1f}s")
                    time.sleep(wait_s)
                    continue
                raise
        raise RuntimeError("Bedrock throttling retry budget exceeded")

    def _build_body(self, user_text: str) -> str:
        if "claude" in self._model_id:
            return json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 220,
                    "temperature": 0.7,
                    "system": self._system_prompt,
                    "messages": [{"role": "user", "content": user_text}],
                }
            )

        return json.dumps(
            {
                "prompt": (
                    "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\\n\\n"
                    f"{self._system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\\n\\n"
                    f"{user_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\\n\\n"
                ),
                "max_gen_len": 220,
                "temperature": 0.7,
                "stop": ["<|eot_id|>", "User:", "\\nUser:", "\\n\\n"],
            }
        )

    def generate_reply(self, user_text: str, intent: str = "chat") -> str:
        if not user_text.strip():
            return "I didn't catch that. Please try again."

        elapsed = time.time() - self._last_call
        if elapsed < self._min_cooldown_sec:
            time.sleep(self._min_cooldown_sec - elapsed)

        client = boto3.client("bedrock-runtime", region_name=self._region)
        body = self._build_body(user_text)

        response = self._invoke_with_backoff(client, body)
        self._last_call = time.time()
        payload = json.loads(response["body"].read())

        if "claude" in self._model_id:
            text = payload["content"][0]["text"].strip()
        else:
            text = payload.get("generation", "").strip()

        return text or "Let's continue."
