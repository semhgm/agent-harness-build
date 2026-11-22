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
AUDIT_PATH = Path(__file__).parent / "logs" / "audit.jsonl"
MODEL = "qwen3:8b-q4_K_M"
POLICY = {
    "listFiles": "allow",
    "readFiles": "allow",
    "writeFiles": "approve",
    "deleteFiles": "approve",
}
def audit(record:dict) -> None:
    AUDIT_PATH.parent.mkdir(exist_ok=True)
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
def guardToolCall(tool_name: str, args: dict, tainted: bool) -> tuple[bool, str, str]:  # ← str bir tane daha
    """Check if the tool call is allowed based on the policy."""

    action = POLICY.get(tool_name)
    if tool_name in ("writeFiles", "deleteFiles") and args.get("fileName", "").strip(". ").lower().endswith(".py"):
        return False, "Access to .py files is denied by policy.", "py_rule"          # ←
    elif tainted and tool_name in ("writeFiles", "deleteFiles"):
        return False, "Session is tainted: untrusted file content was read. Write/delete actions are blocked. Tell the user.", "taint"  # ←
    elif action == "allow":
        return True, f"{tool_name} allowed", "policy_allow"                          # ←
    elif action == "approve":
        confirmation = input(f"Tool '{tool_name}' is requesting to be called with arguments {args}. Do you approve? (y/n): ")
        if confirmation.lower() == "y":
            return True, "approved by user", "user_approved"                         # ←
        return False, "The user explicitly denied this action. Do not retry. Tell the user they declined it.", "user_denied"  # ←
    else:
        print(f"Tool '{tool_name}' is not allowed to be called.")
        return False, f"Tool '{tool_name}' is not allowed to be called.", "unknown_tool"  # ←
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

def writeFiles(fileName: str, content: str) -> str:
    """write a file to the workspace folder."""
    path = (WORKSPACE / fileName).resolve()
    if not path.is_relative_to(WORKSPACE.resolve()):
        return f"Cannot write '{fileName}' outside the workspace."
    path.write_text(content, encoding="utf-8")
    return f"File '{fileName}' written successfully."
def deleteFiles(fileName:str)->str:
    """Delete a file from the workspace folder."""
    path = (WORKSPACE / fileName).resolve()
    if not path.is_relative_to(WORKSPACE.resolve()) or not path.is_file():
        return f"File '{fileName}' not found."
    path.unlink()
    return f"File '{fileName}' deleted successfully."

TOOLS = {
    "listFiles": listFiles,
    "readFiles": readFiles,
    "writeFiles": writeFiles,
    "deleteFiles": deleteFiles,
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
    },
    {
        "type": "function",
        "function": {
            "name": "writeFiles",
            "description": "Write a file to the user's workspace folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fileName": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["fileName", "content"]
            }
        }
    },
    {

        "type": "function",
        "function": {
            "name": "deleteFiles",
            "description": "Delete a file from the user's workspace folder.",
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
    messages = [
        {"role": "system", "content": "You are a file assistant. Only use the provided tools. Never claim you did something unless a tool result confirms it. If no tool can do it, say so. /no_think"},
        {"role": "user", "content": user_input},
    ]
    tainted = False
    turn = 0
    while True:
        turn += 1
        if turn > 5:
            audit({"event": "turn_limit", "turn": turn})
            return "Çok fazla tur oldu, durdum."

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            answer = message.content or "No response from the model."
            audit({"event": "final_answer", "turn": turn, "answer": answer})
            return answer

        messages.append(message)
        for call in message.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            print(f" [tool]{call.function.name}({args})")

            tainted_before = tainted
            allowed, reason, rule = guardToolCall(call.function.name, args, tainted)
            if call.function.name == "readFiles" and allowed:  # Eğer readFiles çağrıldıysa ve izin verildiyse
                tainted = True  # Tainted durumunu True yap
            if allowed:                                                  # 2. kontrol et
                result = TOOLS[call.function.name](**args)
            else:
                result = f"Blocked by policy: {reason}"
            audit({                                                     # ← AŞAĞIYA TAŞINDI
                "event": "tool_call",                                   # ← YENİ
                "turn": turn,                                           # ← YENİ
                "tool": call.function.name,
                "args": args,
                "allowed": allowed,
                "rule": rule,
                "tainted": tainted_before,                              # ← tainted değil, tainted_before
                "result": result[:200],                                 # ← YENİ
            })
            

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result
            })

    
if __name__ == "__main__":
    print(f"this is v1 ({MODEL}) ctrl+c to exit")
    try:
        while True:
            question = input("You: \n")
            print("Assistant: \n" + chat(question))
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")
