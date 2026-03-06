"""
CS 5542 — Week 8 Lab: Inference with LoRA-adapted Model
Load the fine-tuned adapter and run domain-specific inference.
"""

import json
import os
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Paths
BASE_MODEL = "unsloth/Llama-3.2-1B-Instruct"
ADAPTER_DIR = os.path.join(os.path.dirname(__file__), "adapters")


def load_model(adapter_dir: str = ADAPTER_DIR, base_model: str = BASE_MODEL):
    """Load base model with LoRA adapter merged."""
    print(f"Loading base model: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )

    if os.path.exists(os.path.join(adapter_dir, "adapter_config.json")):
        print(f"Loading LoRA adapter from: {adapter_dir}")
        model = PeftModel.from_pretrained(model, adapter_dir)
        model = model.merge_and_unload()
        print("Adapter merged successfully.")
    else:
        print("WARNING: No adapter found. Running base model only.")

    model.eval()
    return model, tokenizer


def generate(model, tokenizer, instruction: str, input_text: str = "",
             max_new_tokens: int = 512, temperature: float = 0.1) -> dict:
    """Generate a response for a cybersecurity instruction."""
    if input_text:
        prompt = f"""### Instruction:
{instruction}

### Input:
{input_text}

### Response:
"""
    else:
        prompt = f"""### Instruction:
{instruction}

### Response:
"""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    start = time.perf_counter()

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.pad_token_id,
        )

    latency_ms = (time.perf_counter() - start) * 1000
    response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    return {
        "instruction": instruction,
        "input": input_text,
        "response": response.strip(),
        "latency_ms": round(latency_ms, 1),
        "tokens_generated": outputs.shape[1] - inputs["input_ids"].shape[1],
    }


def main():
    model, tokenizer = load_model()

    test_queries = [
        {"instruction": "Classify this SSH session as human or automated.", "input": "Commands: whoami, ls -la, cat /etc/passwd, uname -a, w, last"},
        {"instruction": "What are the MITRE ATT&CK tactics for credential dumping?", "input": ""},
        {"instruction": "Analyze this brute force pattern.", "input": "50 failed SSH logins from 192.168.1.100 in 30 seconds targeting root account"},
        {"instruction": "Write a Snowflake query to find top attacking IPs.", "input": ""},
    ]

    results = []
    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"Q: {q['instruction']}")
        if q["input"]:
            print(f"Input: {q['input']}")
        result = generate(model, tokenizer, q["instruction"], q["input"])
        print(f"A: {result['response'][:200]}...")
        print(f"Latency: {result['latency_ms']}ms | Tokens: {result['tokens_generated']}")
        results.append(result)

    out_path = os.path.join(os.path.dirname(__file__), "results", "inference_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
