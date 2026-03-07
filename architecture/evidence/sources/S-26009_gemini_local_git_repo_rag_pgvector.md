---
id: S-26009
title: "Gemini — Local Git Repo RAG Setup with pgvector"
date: 2026-03-08
model: gemini-3-flash
extracted_into: A-26006
---

How to create a RAG based on the git repo? I have already a repo, files that I need. I have ollama and local LLMs I can run using ollama and aider via CLI or Open WebUI interface.

Building a local RAG (Retrieval-Augmented Generation) system over a Git repository is a great way to talk to your code without sending proprietary data to the cloud. Since you already have Ollama and Open WebUI, you have the hardest parts already configured.

Here is the most efficient way to set this up using your existing stack.

Option 1: Using Open WebUI (Easiest)
Open WebUI has built-in RAG capabilities. It handles the document parsing, vector storage (ChromaDB), and retrieval logic automatically.

Prepare your Repo: Open WebUI can ingest local files or URLs. If your repo is local, zip the important directories or simply select the files.

Upload to Workspace:

Go to Workspace > Documents.

Click the + button and upload your source code files.

Chat with the Repo:

Start a new chat.

Type # followed by the name of the document/collection you just uploaded.

Ask your question (e.g., "How does the authentication logic work in this repo?").

Option 2: Using Aider (Best for Coding)
Since you mentioned Aider, you actually have a "high-context" RAG-like system ready to go. Aider doesn't just "read" the files; it understands the repo structure using a repo map.

Navigate to your repo: cd /path/to/your/repo

Launch Aider with Ollama:

Bash
aider --model ollama/llama3.1  # Or your preferred local model
Add Files to Context: Aider works best when you explicitly add files you're interested in using /add <filename>, but it will automatically reference the "repo map" to find relevant context across the whole project.

Option 3: DIY Python Script (For Full Control)
If you want to build a custom pipeline to process the Git history or specific branches, you can use LangChain or LlamaIndex with Ollama.

The Logic Flow:
Load: Use GitLoader to pull files from your local path.

Split: Break code into chunks (usually by function or class).

Embed: Use an embedding model via Ollama (e.g., nomic-embed-text).

Store: Save to a local vector store like Chroma or FAISS.

Query: Send the user prompt + retrieved code chunks to your local LLM.

Example snippet (Python):
Python
from langchain_community.document_loaders import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language

# Load code
loader = GenericLoader.from_path(
    "./my-repo",
    glob="**/*",
    suffixes=[".py", ".js"],
    parser=LanguageParser(language=Language.PYTHON, parser_threshold=500)
)
docs = loader.load()
Key Tips for Git RAG
Ignore the Noise: Ensure your RAG process ignores .git, node_modules, or venv folders. This saves memory and prevents "hallucinated" dependencies.

Embedding Model: Make sure your embedding model in Open WebUI/Ollama is capable. nomic-embed-text is currently a top-tier choice for local setups.

Context Window: Local models often have smaller context windows. If your repo is huge, lean on Aider, as its repo-mapping technique is more efficient than raw RAG for code.

Would you like me to provide a full Python script to automate the ingestion of your repo into a local vector database?

You said
Open WebUI is static, I want to automatically update the RAG. Aider uses not RAG but real files in the context so if I add the entire repo via /add or /readonly commands my local LLMs will be broken.

You are absolutely right. Loading a massive repo directly into the context (the "stuffing" method) will choke most local LLMs, leading to slowed inference, lost focus, or a total crash.

Since you want automation and efficiency, the best approach is to build a Local Vector Database Pipeline that watches your directory for changes. This keeps your LLM "lean" by only feeding it the specific snippets relevant to your current query.

The "Auto-Updating" RAG Architecture
To avoid manual uploads in Open WebUI, you can use a background script that syncs your Git repo to a vector store.

1. The Strategy: "Watchdog" Sync
Instead of manually clicking upload, you can use a Python script with the watchdog library. Whenever you git pull or save a file, the script:

Detects the change.

Re-chunks only the modified files.

Updates the local Vector DB (ChromaDB or Qdrant).

2. Implementation via LangChain + Ollama
Here is a high-level logic for a script you can run in the background. It uses Nomic for embeddings (which is great for code) and ChromaDB as the "brain."

Python
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Setup Embeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# 2. Define the "Update" function
def update_vector_db():
    loader = DirectoryLoader('./my-repo', glob="**/*.py") # Adjust extension
    docs = loader.load()

    # Code-aware splitting is crucial
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)

    # Persistent local DB
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    print("Vector DB Updated.")

# You can trigger update_vector_db() via a file watcher or a git hook.

3. Integrating with your Tools
For Open WebUI:
Open WebUI can actually connect to an External RAG API.

Instead of uploading files to the WebUI, you can point Open WebUI to a "Functions" script or a separate API (like LocalGPT or a custom FastAPI wrapper) that queries the chroma_db created above.

This keeps the WebUI "dynamic" because the underlying database is being updated by your background script.

For Aider:
Stop using /add . or /readonly .. Instead:

Use Aider's architect mode or simply let it rely on the Repo Map.

Aider automatically creates a .aider.repository.cache which is a mini-graph of your whole repo. It's not RAG, but it's "RAG-lite." It sends only the signatures (classes/functions) to the LLM, and only pulls in full code when it needs to edit.

Recommended Stack for "Set and Forget"
Component	Recommendation	Why?
Watcher	watchdog (Python)	Triggers updates on every file save/git pull.
Embedding	nomic-embed-text	Specifically trained for long context and code.
Vector DB	ChromaDB	Runs locally as a folder; no server setup required.
Orchestrator	Verba or AnythingLLM	Both have "Desktop" versions that can "Watch" a local folder and update the RAG automatically.
Would you like me to write a complete Python "Watcher" script that you can leave running in a terminal to keep your local vector DB synced with your Git repo?

You said
So, RAG is just a broad term? There is no a concrete technology under this term?

Spot on. RAG is an architectural pattern, not a specific software package or a single line of code. It's a "strategy" for giving an LLM a temporary, high-speed memory upgrade.

The "Standard" Ingredients
While RAG is a concept, it is almost always built using a specific workflow often called the ETL Pipeline (Extract, Transform, Load):

The Parser: A tool to read your files (PDF, Python, Markdown).

The Chunker: A logic that breaks a 1,000-line code file into smaller, digestible pieces (e.g., 50-line chunks).

The Embedding Model: A mathematical "translator" (like nomic-embed-text) that converts text into Vectors (long lists of numbers).

The Vector Database: A specialized database (ChromaDB, Qdrant, Milvus) that stores those numbers and allows for "semantic search" (finding code by meaning, not just keywords).

The Orchestrator: The glue (LangChain, LlamaIndex, or even a simple Python script) that takes your question, looks up the relevant chunks in the DB, and stuffs them into the LLM prompt.

You said
I need a RAG I can maintain on the server so my agent can use it when I prompt it.

Since you need a server-side RAG that stays updated and acts as a "source of truth" for your agents, you are looking for a Back-end Vector Service.

You said
and how about pgvector plugin for Postgres?

Using pgvector is a brilliant "pro" move. It allows you to treat your RAG data like any other row in a database, which solves your "static" problem. Instead of a messy folder of JSON files, you have a professional SQL table that supports ACID transactions and complex queries.

Here is how pgvector changes the game for your server-side agent:

1. Why pgvector?
Unified Data: You can store the code snippet, the file path, the Git commit hash, and the vector embedding all in one row.

Easy Updates: To update your RAG, you just run an UPDATE or INSERT SQL command. No need to re-index the entire "collection."

Filtering: You can ask the LLM to search only in .py files or only in a specific directory by adding a simple WHERE clause to your vector search.

2. The Implementation (Server-Side)
Install pgvector: If you use Docker, use the pgvector/pgvector:pg16 image.

Initialize:

SQL
CREATE EXTENSION vector;
CREATE TABLE code_vectors (
    id serial PRIMARY KEY,
    file_path TEXT,
    content TEXT,
    commit_sha TEXT,
    embedding vector(768) -- Matches nomic-embed-text dimensions
);

The Automated "Sync" Script:
You can run a script that checks for the latest git commit. If it's new, it chunks the changed files and updates Postgres.

You said
should I create different RAGs for different repos or combine them into one vector database?

The Recommendation: "One Database, Different Collections"
Don't create entirely separate database instances (Postgres clusters) for each repo. Instead, use a Single Database with a Metadata Column to distinguish between repos.

Why a Single Database?
Lower Overhead: You only maintain one Postgres instance, one backup routine, and one Ollama connection.

Cross-Repo Intelligence: If Repo A uses a library from Repo B, your agent can search across both to understand the full stack trace.

Simplicity: Your connection string stays the same for all your agents.

You said
and how about creating different schemas instead of one huge table? will it help to reduce maintenance burden of reindexation and other administrative stuff?

Using Postgres Schemas is a very sophisticated middle ground. It offers the logical isolation of separate databases with the administrative ease of a single instance.

Does it reduce the maintenance burden?
The short answer is yes, significantly, especially regarding index management and data lifecycle.

1. Granular Re-indexing
Vector indexes (like HNSW) are computationally expensive to build.

One Huge Table: If you add 10,000 lines of code to "Repo A," the database has to update the index for the entire table of 1,000,000 lines.

Different Schemas: You index each table independently. Re-indexing the "Frontend" schema won't touch the "Backend" index.

2. Instant "Cleanup"
One Huge Table: DELETE FROM... WHERE repo_id = X leaves "bloat" requiring VACUUM.

Different Schemas: DROP SCHEMA repo_x CASCADE; is instantaneous.

You said
and you said pgvector is good only for <1M chunks, so it is a tech debt in case of scalability, correct?

"Technical debt" is a strong term. The idea that pgvector is "only good for <1M chunks" is a common benchmark threshold where performance starts to diverge from specialized databases. However, calling it technical debt depends on your ultimate goal.

1M limit is per-index, not per-database. With schema-per-repo, each index stays lean.

2026 reality: halfvec (half-precision) and pgvectorscale (Rust-based) now allow Postgres to handle 50M+ vectors with sub-100ms latency.

The real bottleneck: embedding model latency (~300ms) dwarfs vector search (~5ms). Optimizing the database choice is often premature optimization.

Migration path: Exporting from Postgres to Qdrant/Milvus is a straightforward ETL script — not a structural nightmare.

You said
Write a detailed report on choosing pgvector for RAG considering alternatives and tech debt considerations we have discussed.

Strategic Assessment: Adopting pgvector for Git-Based RAG

1. Executive Summary
PostgreSQL with the pgvector extension is the recommended baseline due to its structural maturity, metadata handling, and recent breakthroughs in high-throughput scaling.

2. Competitive Landscape
Feature	pgvector (Postgres)	Qdrant / Milvus	Chroma
Primary Strength	SQL Integration & ACID	Sub-10ms tail latency	Rapid Prototyping
Throughput	Highest (with pgvectorscale)	High	Moderate
Complexity	Low (if you know SQL)	High (Distributed logic)	Minimal
Metadata	Unlimited SQL joins	Limited "Payloads"	Basic
2026 Scale	50M+ vectors (Production)	1B+ vectors (Enterprise)	<1M (Edge/Local)

The "Bottleneck" Reality:
Recent 2026 benchmarks show that for local RAG, the Vector DB search usually takes ~5ms, while Ollama embedding takes 300ms+.

3. The Schema-Based Architecture
Benefits of Schemas over Tables:
Isolated Re-indexing: Rebuild HNSW index for one schema without affecting others.
Instant Cleanup: DROP SCHEMA repo_x CASCADE; physically removes data immediately.
Logical Ownership: Agent restricted to specific schemas via standard Postgres Roles (RBAC).

7. Final Recommendation
Start with PostgreSQL + pgvector using a Schema-per-Repo design. This minimizes moving parts while providing a clear migration path to a specialized DB should vector count exceed 10 million.
