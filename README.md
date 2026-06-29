# Advanced BERT Sentiment & Summary Analyzer

This project is an advanced sentiment classifier and product reviews summarizer built with PyTorch, Hugging Face Transformers, and local generative models. It runs fully local and offline on your GPU.
# Datasets
flipkart_product.csv 
https://www.kaggle.com/datasets/mansithummar67/flipkart-product-review-dataset

IMDB Dataset 
https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews

Dataset-SA.csv
https://www.kaggle.com/datasets/niraliivaghani/flipkart-product-customer-reviews-dataset


## Core Features
1. **Fine-Grained Sentiment Classifier (5 Levels):** Fine-tuned `distilbert-base-uncased` to classify reviews into:
   - `Very Negative` (0)
   - `Negative` (1)
   - `Neutral` (2)
   - `Positive` (3)
   - `Very Positive` (4)
2. **Local Review Summarization & Pros/Cons Extraction:** Offline summarization powered by `Qwen/Qwen2.5-1.5B-Instruct` running local on CUDA. It compiles a batch of reviews to generate a paragraph summary and a list of key Pros and Cons.

---

## Getting Started

### 1. Pre-requisites & GPU setup
Ensure your Python virtual environment uses **Python 3.11** (recommended for package stability) and install PyTorch with CUDA 12.1:
```bash
# Set up venv
C:\Users\datta\AppData\Local\Programs\Python\Python311\python.exe -m venv .venv

# Activate venv (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install PyTorch with CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Install requirements
pip install pandas scikit-learn transformers accelerate
```

---

### 2. Preprocess & Clean Datasets
Make sure your raw datasets (`Dataset-SA.csv`, `flipkart_product.csv`, `IMDB-Dataset.csv`, and `test.csv`) are located in the root folder. Then, execute the data preparation script:
```bash
python prepare_data.py
```
This merges training data into `train_clean.csv` and testing data into `test_clean.csv`, aligning all ratings and classifications to a unified 5-class scale.

---

### 3. Train the Sentiment Model
Run training using the fine-tuning script. By default, it trains on a subset of 30,000 rows to ensure rapid training, but you can configure the size:
```bash
# Train on default subset (30k train, 5k validation)
python train.py

# Train on a custom size (e.g. 50k train, 10k validation)
python train.py --train_size 50000 --test_size 10000 --epochs 3 --batch_size 16
```
The fine-tuned model and tokenizer will be saved in `saved_model/`.

---

### 4. Run Predictions & Summarization
You can run inference using the interactive or batch execution options.

#### Single Text Classification:
```bash
python predictions.py --text "This product exceeded my expectations! Battery lasts forever."
```

#### Interactive Console Mode:
```bash
python predictions.py --interactive
```

#### Batch File Analysis & Summarization (Local LLM):
Run predictions on a batch of reviews (either a `.csv` file or a `.txt` file with one review per line). Use the `--summarize` flag to generate a summary and a bulleted list of Pros and Cons using `Qwen/Qwen2.5-1.5B-Instruct`:
```bash
# Run sentiment classification on all reviews in a file
python predictions.py --batch_file test_clean.csv --column Review

# Run sentiment and generate an offline summary + pros/cons list
python predictions.py --batch_file test_clean.csv --column Review --summarize
```
# How to Run
## Prerequisites

Make sure you have the following installed:

- Node.js (v18 or later recommended)
- npm
- Python 3.10+
- pip

---
# Frontend Setup

Navigate to the frontend directory.

```bash
cd frontend
```

Install dependencies.

```bash
npm install
```

Start the development server.

```bash
npm run dev
```

The frontend will be available at

```
http://localhost:5173
```

---

# Backend Setup

Navigate to the backend directory.

```bash
cd backend
```

(Optional) Create a virtual environment.

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

Install the required packages.

```bash
pip install -r requirements.txt
```

Run the backend server.

```bash
python main.py
```
