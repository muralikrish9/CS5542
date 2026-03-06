"""
CS 5542 — Week 8 Lab
LoRA Fine-Tuning Script for Cybersecurity Domain Adaptation

Fine-tunes Llama-3.2-1B-Instruct using LoRA (Low-Rank Adaptation)
on a curated cybersecurity/honeypot instruction dataset.

Designed to run on Google Colab free tier (T4 GPU).

Usage:
    # On Colab:
    !pip install unsloth datasets trl
    %run fine_tune.py

    # Local (with GPU):
    python fine_tune.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_MODEL = "unsloth/Llama-3.2-1B-Instruct"
DATASET_PATH = os.path.join(os.path.dirname(__file__), "data", "instructions.jsonl")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "adapters")
MAX_SEQ_LENGTH = 2048
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3
BATCH_SIZE = 4
GRADIENT_ACCUMULATION = 2
WARMUP_STEPS = 10
LOGGING_STEPS = 5
SAVE_STEPS = 50


def load_instruction_dataset(path: str) -> list[dict]:
    """Load instruction-response pairs from JSONL file."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    print(f"Loaded {len(records)} instruction pairs from {path}")
    return records


def format_instruction(sample: dict) -> str:
    """Format a single instruction sample into Llama-3 chat format."""
    instruction = sample["instruction"]
    inp = sample.get("input", "")
    output = sample["output"]

    if inp:
        user_msg = f"{instruction}\n\nInput: {inp}"
    else:
        user_msg = instruction

    return (
        "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        "You are a cybersecurity analyst specializing in honeypot data analysis, "
        "attack classification, and threat assessment. You have expertise in "
        "Snowflake SQL queries for security analytics.<|eot_id|>"
        "<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_msg}<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>\n\n"
        f"{output}<|eot_id|>"
    )


def main():
    """Run LoRA fine-tuning pipeline."""
    print("=" * 60)
    print("CS 5542 — Week 8: LoRA Fine-Tuning for Cybersecurity")
    print("=" * 60)

    # --- Step 1: Load dataset ---
    raw_data = load_instruction_dataset(DATASET_PATH)

    # --- Step 2: Try Unsloth (fast path), fall back to PEFT ---
    try:
        from unsloth import FastLanguageModel
        print(f"\nLoading base model via Unsloth: {BASE_MODEL}")

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=BASE_MODEL,
            max_seq_length=MAX_SEQ_LENGTH,
            load_in_4bit=True,
            dtype=None,
        )

        model = FastLanguageModel.get_peft_model(
            model,
            r=LORA_R,
            lora_alpha=LORA_ALPHA,
            lora_dropout=LORA_DROPOUT,
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj",
            ],
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=42,
        )
        use_unsloth = True
        print("Unsloth LoRA model ready.")

    except ImportError:
        print("Unsloth not available — falling back to PEFT + Transformers")
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import LoraConfig, get_peft_model

        tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Llama-3.2-1B-Instruct",
            trust_remote_code=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Llama-3.2-1B-Instruct",
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=True,
        )

        lora_config = LoraConfig(
            r=LORA_R,
            lora_alpha=LORA_ALPHA,
            lora_dropout=LORA_DROPOUT,
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj",
            ],
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_config)
        use_unsloth = False
        print("PEFT LoRA model ready.")

    model.print_trainable_parameters()

    # --- Step 3: Prepare training data ---
    from datasets import Dataset

    formatted = [{"text": format_instruction(s)} for s in raw_data]
    dataset = Dataset.from_list(formatted)
    print(f"Training dataset: {len(dataset)} samples")

    # --- Step 4: Train ---
    from trl import SFTTrainer
    from transformers import TrainingArguments

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        logging_steps=LOGGING_STEPS,
        save_steps=SAVE_STEPS,
        save_total_limit=2,
        fp16=True,
        optim="adamw_8bit" if use_unsloth else "adamw_torch",
        seed=42,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        max_seq_length=MAX_SEQ_LENGTH,
    )

    print("\nStarting LoRA fine-tuning...")
    train_result = trainer.train()
    print(f"\nTraining complete. Loss: {train_result.training_loss:.4f}")

    # --- Step 5: Save LoRA adapter ---
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"LoRA adapter saved to {OUTPUT_DIR}/")

    # Save training metadata
    meta = {
        "base_model": BASE_MODEL,
        "lora_r": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "lora_dropout": LORA_DROPOUT,
        "num_epochs": NUM_EPOCHS,
        "learning_rate": LEARNING_RATE,
        "training_samples": len(dataset),
        "training_loss": round(train_result.training_loss, 4),
    }
    meta_path = os.path.join(OUTPUT_DIR, "training_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Training metadata saved to {meta_path}")

    print("\n" + "=" * 60)
    print("Fine-tuning pipeline complete!")
    print(f"  Adapter:  {OUTPUT_DIR}/")
    print(f"  Samples:  {len(dataset)}")
    print(f"  Loss:     {train_result.training_loss:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
