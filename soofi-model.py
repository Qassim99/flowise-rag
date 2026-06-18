import json

import requests

url = "https://soofi-owu.l3s.de/api/chat/completions"

headers = {
    "Authorization": "Bearer sk-ed443de23ce34d09b86ca3ef4df325f4",
    "Content-Type": "application/json",
}

payload = {
    "model": "sft_Soofi_Nano_30B_A3B_nemotron_posttrain_v3_em_v2_cleaned_bridge__iter_0000600",
    "messages": [
        {
            "role": "system",
            "content": (
                "Return only valid JSON. No markdown. No explanation. "
                "The JSON must have exactly two keys: "
                "rewritten_question and detected_language."
            ),
        },
        {"role": "user", "content": "Wie kann ich meine Steuererklärung abgeben?"},
    ],
    "temperature": 0,
    "max_tokens": 128,
    "chat_template_kwargs": {"enable_thinking": False},
}

r = requests.post(url, headers=headers, json=payload, verify=False)

print("STATUS:", r.status_code)
data = r.json()
print(json.dumps(data, indent=2, ensure_ascii=False))

content = data["choices"][0]["message"]["content"]
print("\nASSISTANT CONTENT:")
print(content)

try:
    parsed = json.loads(content)
    print("\nPARSED JSON:")
    print(parsed)
except Exception as e:
    print("\nJSON PARSE ERROR:", e)
