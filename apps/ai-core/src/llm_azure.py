from openai import AzureOpenAI
from settings import settings

_client = None

def get_client():
    global _client
    if _client is None:
        _client = AzureOpenAI(
            api_key=settings.azure_api_key,
            azure_endpoint=settings.azure_endpoint,
            api_version=settings.azure_api_version,
        )
    return _client

def chat_completion(system: str, user: str, max_tokens: int = 900, temperature: float = 0.2) -> str:
    client = get_client()
    resp = client.chat.completions.create(
        model=settings.azure_deployment,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content
