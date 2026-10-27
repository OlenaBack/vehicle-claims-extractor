"""Build initial and repair messages for structured extraction."""


class PromptBuilder:
    def __init__(self, system_prompt: str, repair_prompt: str):
        self._system_prompt = system_prompt
        self._repair_prompt = repair_prompt

    def initial(self, text: str) -> list[dict]:
        return [
            {"role": "system", "content": self._system_prompt},
            {
                "role": "user",
                "content": f"<description>\n{text}\n</description>",
            },
        ]

    def repair(
        self,
        messages: list[dict],
        content: str,
        error: str,
    ) -> list[dict]:
        return [
            *messages,
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": self._repair_prompt.replace("{error}", error),
            },
        ]
