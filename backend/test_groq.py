import asyncio
import traceback

from openai import AsyncOpenAI
from core.config import settings


async def main():
    print("STEP 1: Starting", flush=True)
    print(f"STEP 2: Model = {settings.GROQ_MODEL}", flush=True)
    print(f"STEP 3: API key loaded = {bool(settings.GROQ_API_KEY)}", flush=True)

    client = AsyncOpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )

    print("STEP 4: Client created", flush=True)
    print("STEP 5: Sending request...", flush=True)

    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with exactly: GROQ WORKING"
                }
            ],
            max_tokens=50,
        )

        print("STEP 6: Response received", flush=True)
        print(
            "STEP 7:",
            response.choices[0].message.content,
            flush=True
        )

    except Exception as e:
        print("ERROR:", type(e).__name__, flush=True)
        print("MESSAGE:", str(e), flush=True)
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
