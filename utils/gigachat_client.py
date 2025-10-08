from gigachat import GigaChat
from gigachat.models import Chat
import logging

class GigaChatClient:

    def __init__(
        self,
        credentials: str,
        model: str = "GigaChat",
        verify_ssl_certs: bool = False
    ):
        self.credentials = credentials
        self.model = model
        self.verify_ssl_certs = verify_ssl_certs
        self.giga = GigaChat(
            credentials=credentials,
            model=model,
            verify_ssl_certs=verify_ssl_certs
        )

    async def chat(
        self,
        message: str
    ) -> str:
        logging.info(f"Prompt sent to AI: {message}")
        response: Chat = self.giga.chat(message)
        logging.info(f"AI response: {response.choices[0].message.content} ({response.usage.prompt_tokens} tokens)")
        return response.choices[0].message.content

    def close(self):
        self.giga.close()