"""Build initial and repair messages for structured extraction."""


class PromptBuilder:
    def __init__(self, system_prompt: str, repair_prompt: str):
        self._system_prompt = system_prompt
        self._repair_prompt = repair_prompt

    def initial(self, accident_description: str) -> list[dict]:
        return [
            {"role": "system", "content": self._system_prompt},
            {
                "role": "user",
                "content": f"<description>\n{accident_description}\n</description>",
            },
        ]

    def repair(
        self,
        messages: list[dict],
        previous_response: str,
        validation_error: str,
    ) -> list[dict]:
        return [
            *messages,
            {"role": "assistant", "content": previous_response},
            {
                "role": "user",
                "content": self._repair_prompt.replace("{error}", validation_error),
            },
        ]
