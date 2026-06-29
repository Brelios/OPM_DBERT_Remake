import os
import argparse
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)

class SentimentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.texts = list(texts)
        self.labels = list(labels)
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = int(self.labels[idx])
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    # Calculate precision, recall, f1, and accuracy
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average='macro', zero_division=0
    )
    acc = accuracy_score(labels, predictions)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def main():
    parser = argparse.ArgumentParser(description="Train a 5-class BERT Sentiment Classifier.")
    parser.add_argument("--train_path", type=str, default="train_clean.csv", help="Path to cleaned training data")
    parser.add_argument("--test_path", type=str, default="test_clean.csv", help="Path to cleaned testing data")
    parser.add_argument("--model_name", type=str, default="distilbert-base-uncased", help="Base model architecture")
    parser.add_argument("--train_size", type=int, default=30000, help="Number of rows to sample for training (0 for all)")
    parser.add_argument("--test_size", type=int, default=5000, help="Number of rows to sample for evaluation (0 for all)")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Training batch size")
    parser.add_argument("--max_len", type=int, default=128, help="Max sequence length for tokenization")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--saved_model_dir", type=str, default="saved_model", help="Directory to save the trained model")
    parser.add_argument("--output_dir", type=str, default="results", help="Directory to store training logs/checkpoints")
    args = parser.parse_args()

    # Verify input datasets exist
    if not os.path.exists(args.train_path) or not os.path.exists(args.test_path):
        print(f"Error: Preprocessed datasets not found. Please run prepare_data.py first.")
        return

    print("Loading preprocessed training data...")
    df_train = pd.read_csv(args.train_path)
    df_test = pd.read_csv(args.test_path)

    # Sample datasets if requested
    if args.train_size > 0 and args.train_size < len(df_train):
        print(f"Subsetting training data to {args.train_size} rows...")
        df_train = df_train.sample(n=args.train_size, random_state=42).reset_index(drop=True)
    if args.test_size > 0 and args.test_size < len(df_test):
        print(f"Subsetting testing data to {args.test_size} rows for evaluation...")
        df_test = df_test.sample(n=args.test_size, random_state=42).reset_index(drop=True)

    print(f"Training dataset shape: {df_train.shape}")
    print(f"Testing dataset shape: {df_test.shape}")
    print("Training labels distribution:")
    print(df_train['Label'].value_counts())

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using execution device: {device.upper()}")

    print(f"Loading pre-trained tokenizer & model for {args.model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    # We have 5 label classes (0: Very Neg, 1: Neg, 2: Neu, 3: Pos, 4: Very Pos)
    model = AutoModelForSequenceClassification.from_pretrained(args.model_name, num_labels=5)
    model.to(device)

    print("Preparing tokenized PyTorch Datasets...")
    train_dataset = SentimentDataset(df_train['Review'], df_train['Label'], tokenizer, args.max_len)
    test_dataset = SentimentDataset(df_test['Review'], df_test['Label'], tokenizer, args.max_len)

    print("Configuring TrainingArguments...")
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_ratio=0.1,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=100,
        eval_strategy='epoch',
        save_strategy='epoch',
        load_best_model_at_end=True,
        metric_for_best_model='accuracy',
        fp16=torch.cuda.is_available(), # Mixed precision speeds up RTX 4060 training dramatically
        report_to="none"
    )

    print("Initializing Trainer...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )

    print("Starting training process...")
    trainer.train()

    print(f"Evaluating the best model on test dataset...")
    eval_results = trainer.evaluate()
    print("Evaluation Results:", eval_results)

    print(f"Saving final fine-tuned model and tokenizer to {args.saved_model_dir}...")
    model.save_pretrained(args.saved_model_dir)
    tokenizer.save_pretrained(args.saved_model_dir)
    print("Save complete! Ready for predictions.")

if __name__ == "__main__":
    main()
