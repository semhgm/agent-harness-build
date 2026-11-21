import sys
sys.stdout.reconfigure(encoding='utf-8') #for the emoji crash!
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",  # OpenAI yerine senin bilgisayarın
    api_key="ollama"                        # gerçek key gerekmiyor, herhangi bir şey yaz
)
MODEL = "qwen3:8b-q4_K_M"

def chat(user_input: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
        ],
        max_tokens=2000
    )
    return response.choices[0].message.content or "No response from the model."

if __name__ == "__main__":
    print("this is v0 ({MODEL}) ctrl+c to exit")
    try:
        while True:
            question = input("You: \n")
            print("Assistant: \n" + chat(question))
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")
