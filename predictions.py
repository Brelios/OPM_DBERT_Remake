import os
import argparse
import sys
import torch
import numpy as np
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM

# Set standard output encoding to utf-8 to avoid console print crashes on Windows
sys.stdout.reconfigure(encoding='utf-8')

# Map labels back to human readable categories
LABEL_MAP = {
    0: "Very Negative",
    1: "Negative",
    2: "Neutral",
    3: "Positive",
    4: "Very Positive"
}

# Color formatting helpers for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def get_label_color(label_str):
    if label_str in ["Very Positive", "Positive"]:
        return Colors.GREEN
    elif label_str == "Neutral":
        return Colors.YELLOW
    else:
        return Colors.RED

class SentimentAnalyzer:
    def __init__(self, model_dir="saved_model"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_dir = model_dir
        self.tokenizer = None
        self.model = None
        self.llm_model = None
        self.llm_tokenizer = None

        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"Trained BERT model not found in '{model_dir}'. Please run train.py first.")

        print(f"Loading custom sentiment classifier from '{model_dir}' on {self.device.upper()}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self.model.to(self.device)
        self.model.eval()

    def predict(self, text: str) -> dict:
        """Predict sentiment label and confidence score for a single review."""
        if not text.strip():
            return {"label": "Neutral", "confidence": 1.0, "scores": [0.0]*5}
            
        inputs = self.tokenizer(
            text,
            max_length=128,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
            
        pred_class = int(np.argmax(probs))
        label_str = LABEL_MAP[pred_class]
        confidence = float(probs[pred_class])
        
        return {
            "label": label_str,
            "confidence": confidence,
            "probs": probs.tolist()
        }

    def load_summarizer(self, llm_name="Qwen/Qwen2.5-1.5B-Instruct"):
        """Lazy load the generative model for summarization and aspect extraction."""
        if self.llm_model is not None:
            return

        print(f"\nLoading local summarization model '{llm_name}' on {self.device.upper()} (this may take a minute first-time)...")
        self.llm_tokenizer = AutoTokenizer.from_pretrained(llm_name)
        # Load in fp16 if GPU is available to save VRAM (requires ~3GB VRAM)
        self.llm_model = AutoModelForCausalLM.from_pretrained(
            llm_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        print("Summarizer model loaded successfully!")

    def summarize_reviews(self, reviews: list) -> str:
        """Generate a text summary and pros/cons lists from a list of reviews."""
        self.load_summarizer()
        
        # Consolidate reviews into a single block
        reviews_text = "\n".join([f"- {r}" for r in reviews[:30]])  # Limit to top 30 reviews to avoid context blowup
        
        system_prompt = (
            "You are an expert product review analyst. Your task is to summarize the customer feedback "
            "provided below and extract a bulleted list of Pros (things customers liked) and Cons (things customers disliked). "
            "Keep the summary concise (2-3 sentences) and write 3-5 realistic pros and cons based strictly on the reviews. "
            "Do not invent any facts."
        )
        
        user_prompt = f"Here are the customer reviews for a product:\n{reviews_text}\n\nPlease generate the Summary, Pros, and Cons."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        text = self.llm_tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = self.llm_tokenizer([text], return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            generated_ids = self.llm_model.generate(
                **model_inputs,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True
            )
            # Trim inputs from generated output
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            response = self.llm_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
        return response.strip()

def print_distribution(counts, total):
    print(f"\n{Colors.BOLD}Sentiment Distribution:{Colors.END}")
    for val, name in LABEL_MAP.items():
        count = counts.get(name, 0)
        pct = (count / total) * 100 if total > 0 else 0
        color = get_label_color(name)
        bar = "█" * int(pct // 5)
        print(f"  {color}{name:<15}{Colors.END}: {count:>4} ({pct:>5.1f}%) {color}{bar}{Colors.END}")

def main():
    parser = argparse.ArgumentParser(description="Analyze reviews using custom BERT and local LLM.")
    parser.add_argument("--text", type=str, help="Single review text to predict sentiment on")
    parser.add_argument("--batch_file", type=str, help="Path to text/CSV file containing multiple reviews")
    parser.add_argument("--column", type=str, default="Review", help="Column name if loading batch reviews from a CSV")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive single-prediction loop")
    parser.add_argument("--model_dir", type=str, default="saved_model", help="Directory where custom BERT is saved")
    parser.add_argument("--summarize", action="store_true", help="When running batch reviews, generate summary + pros/cons")
    args = parser.parse_args()

    try:
        analyzer = SentimentAnalyzer(args.model_dir)
    except FileNotFoundError as e:
        print(e)
        return

    # Mode 1: Single text input
    if args.text:
        res = analyzer.predict(args.text)
        color = get_label_color(res["label"])
        print(f"\n{Colors.BOLD}Review:{Colors.END} \"{args.text}\"")
        print(f"{Colors.BOLD}Sentiment:{Colors.END} {color}{res['label']}{Colors.END} (Confidence: {res['confidence']:.2%})")
        return

    # Mode 2: Interactive loop
    if args.interactive:
        print(f"\n{Colors.BOLD}Entering Interactive Mode. Type 'exit' or 'quit' to stop.{Colors.END}")
        while True:
            try:
                text = input(f"\n{Colors.BLUE}Enter review text: {Colors.END}")
                if text.lower().strip() in ['exit', 'quit']:
                    break
                if not text.strip():
                    continue
                res = analyzer.predict(text)
                color = get_label_color(res["label"])
                print(f"{Colors.BOLD}Predicted Sentiment:{Colors.END} {color}{res['label']}{Colors.END} (Confidence: {res['confidence']:.2%})")
            except KeyboardInterrupt:
                break
        return

    # Mode 3: Batch file analysis
    if args.batch_file:
        if not os.path.exists(args.batch_file):
            print(f"Error: Batch file '{args.batch_file}' not found.")
            return

        print(f"Loading reviews from '{args.batch_file}'...")
        reviews = []
        if args.batch_file.endswith('.csv'):
            try:
                df = pd.read_csv(args.batch_file)
                if args.column not in df.columns:
                    print(f"Error: Column '{args.column}' not found in CSV. Available columns: {list(df.columns)}")
                    return
                reviews = df[args.column].dropna().astype(str).tolist()
            except Exception as e:
                print(f"Error reading CSV file: {e}")
                return
        else:
            # Assume plain text file with one review per line
            with open(args.batch_file, 'r', encoding='utf-8') as f:
                reviews = [line.strip() for line in f if line.strip()]

        total_reviews = len(reviews)
        if total_reviews == 0:
            print("No reviews found to analyze.")
            return

        print(f"Analyzing {total_reviews} reviews...")
        counts = {name: 0 for name in LABEL_MAP.values()}
        results = []

        for idx, rev in enumerate(reviews):
            res = analyzer.predict(rev)
            counts[res["label"]] += 1
            results.append((rev, res["label"], res["confidence"]))

        print_distribution(counts, total_reviews)

        # Summarization (optional)
        if args.summarize:
            print(f"\n{Colors.BOLD}Generating Summary and Pros/Cons using local LLM...{Colors.END}")
            # Use all reviews or a sample of reviews if there are many
            summary_output = analyzer.summarize_reviews(reviews)
            print("\n" + "="*50)
            print(f"{Colors.BOLD}PRODUCT INSIGHTS SUMMARY (OFFLINE LLM){Colors.END}")
            print("="*50)
            print(summary_output)
            print("="*50)
        return

    # Default: Show help
    parser.print_help()

if __name__ == "__main__":
    main()
