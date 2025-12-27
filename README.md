# mini-rag

A minimal, modular **Retrieval-Augmented Generation (RAG)** application built with **FastAPI**.  
This project provides an end-to-end pipeline for **document ingestion → chunking → embeddings → vector indexing → semantic retrieval → LLM answering**.

> هدف المشروع: بناء Mini RAG بسيط لكن قابل للتوسعة، مع فصل واضح بين الـ API والـ services والـ clients لتسهيل الصيانة والاختبار.

---

## Requirements

**Python 3.10** (recommended)  
  *(Python 3.8+ can work, but this project targets 3.10 for stability and compatibility.)*

#### Install Python using MiniConda

1) Download and install MiniConda from [here](https://docs.anaconda.com/free/miniconda/#quick-command-line-install)
2) Create a new environment using the following command:

```bash
$ conda create -n mini-rag python=3.10
```
3) Activate the environment:
```bash
$ conda activate mini-rag
```

### (Optional) Setup you command line interface for better readability

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

## Installation

### Install the required packages

```bash
$ pip install -r requirements.txt
```

### Setup the environment variables

```bash
$ cp .env.example .env
```

Set your environment variables in the `.env` file. Like `OPENAI_API_KEY` value.

---

## RAG Workflow (High Level)

### 1) Ingestion / Indexing (Build the Knowledge Base)
1. **Extract text** from the source document(s) (txt / pdf / docx / web, etc.)
2. **Chunking** the text into smaller pieces (documents / chunks)
3. **Embedding** each chunk (convert text → vectors)
4. **Indexing**: store chunks + embeddings + metadata in a **Vector Database** (e.g., LanceDB)

### 2) Retrieval / Answering
1. Convert the **user question** into an embedding
2. **Search** the vector database for the most similar chunks (top-k)
3. **Create a prompt** that includes the question + retrieved context
4. Send the prompt to the **LLM** to generate the final answer
5. Return **answer + sources** (chunk ids / similarity score / metadata)

---