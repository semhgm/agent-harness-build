import sys
sys.stdout.reconfigure(encoding='utf-8') #for the emoji crash!
import json
from pathlib import Path
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",  # OpenAI yerine senin bilgisayarın
    api_key="ollama"                        # gerçek key gerekmiyor, herhangi bir şey yaz
)

WORKSPACE = Path(__file__).parent / "workspace"
MODEL = "qwen3:8b-q4_K_M"

def listFiles() -> str:
    """list the files in the asistant's workspace folder."""
    files = [f.name for f in WORKSPACE.iterdir()]
    return "\n".join(files) or "(empty)"

def readFiles(fileName: str) -> str:
    """read a file from the workspace folder."""
    path = (WORKSPACE / fileName).resolve()
    if not path.is_relative_to(WORKSPACE.resolve()) or not path.is_file():
        return f"File '{fileName}' not found."
    return path.read_text(encoding="utf-8")

TOOLS = {
    "listFiles": listFiles,
    "readFiles": readFiles,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "listFiles",
            "description": "List the files in the user's workspace folder.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "readFiles",
            "description": "Read a file from the user's workspace folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fileName": {"type": "string"}
                },
                "required": ["fileName"]
            }
        }
    }
]

def chat(user_input: str) -> str:
    messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
    ]
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,)
        message = response.choices[0].message
        if not message.tool_calls:
            return message.content or "No response from the model."
        messages.append(message)
        for call in message.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            print(f" [tool]{call.function.name}({args})")
            result = TOOLS[call.function.name](**args)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content":result
            })
        final = client.chat.completions.create(
            model=MODEL,
            messages=messages)
        return final.choices[0].message.content or "No response from the model."
        


    
if __name__ == "__main__":
    print(f"this is v1 ({MODEL}) ctrl+c to exit")
    try:
        while True:
            question = input("You: \n")
            print("Assistant: \n" + chat(question))
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")
