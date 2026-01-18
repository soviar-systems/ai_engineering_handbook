# 1. BPE Tokenizer in pure Python

# <b>Motivation</b>

It is absolutely worth building your own Byte Pair Encoding (BPE) tokenizer from scratch for the explicit purpose of learning the mechanics of LLMs.

For educational purposes, the value gained from this exercise is immense, even though it's inefficient for production.

## Educational Value Proposition

The benefit of building a BPE tokenizer from the ground up lies in understanding the **core data representation and efficiency trade-offs** that underpin modern LLMs, which is crucial for a programmer learning LLMs under the hood.

| Component | Value Gained from Building from Scratch | Production Equivalent |
| --- | --- | --- |
| **BPE Algorithm** | Deep understanding of **token efficiency** (minimizing tokens while maximizing vocabulary coverage) and the greedy merging process. | Optimizing tokenizer hyperparameters (e.g., vocabulary size) in Hugging Face. |
| **Vocabulary Generation** | You control and observe how a vocabulary is created, and how unseen sub-words are handled (the **OOV** problem). | Debugging tokenizer/model mismatch and high token usage in inference. |
| **Pre-tokenization** | Understanding the steps before BPE (e.g., normalization, splitting on whitespace/punctuation). | Implementing standardized data cleaning pipelines in MLOps. |
| **Encoding/Decoding** | Direct manipulation of the mapping between text, sub-word strings, and integer IDs. | Understanding how to integrate custom tokens (e.g., control tokens) into prompts. |

This process directly addresses the foundational question of **how human language is serialized into a numerical format** that a transformer model can process.

## Pitfalls and Efficiency Warnings

As you are building this for education, be aware of where real-world systems diverge:

* **Computational Inefficiency:** Your from-scratch Python implementation will be **orders of magnitude slower** than industrial solutions like the Hugging Face `tokenizers` library (which is optimized in Rust). Your code will struggle with a corpus of more than a few thousand documents.
* **Edge Cases:** Truly robust BPE (like that used in GPT or Llama) uses **Byte-Level BPE (BBPE)** to handle *all* possible characters, including those in different languages or emojis, without relying on initial character-level tokenization. You can skip BBPE initially, but understand it's the required complexity for a production-level universal tokenizer.
* **Architectural Overlap:** Understand that in the **PyTorch/TensorFlow** framework, the tokenizer is a **pre-processing utility**, and the *embedding layer* is a separate, trainable component *within* the neural network that maps those integer IDs to dense vectors. **You are building the pre-processing unit, not the embedding layer itself.**

# <b>1.1 Byte-Pair Encoding (BPE) - Our Starting Point</b>

**So what is a tokenizer?** Think of it as the "first contact" between human language and the neural network. It's how we convert raw text into numerical tokens that our model can process.

BPE is beautifully simple yet powerful. Let me explain it with an analogy:

Imagine you're learning a new language by starting with individual letters, then discovering common letter combinations, then whole words, and eventually common phrases. That's essentially what BPE does!

Here's how it works:

1. **Start with basics**: Begin with individual characters as your initial "vocabulary"
2. **Find patterns**: Look for the most frequent pairs of existing tokens
3. **Merge them**: Combine those frequent pairs into new tokens
4. **Repeat**: Keep doing this until you reach your desired vocabulary size

Let me show you a simple example. Suppose we have this text:
```
"low lower lowest"
```

The BPE process would discover that "lo", "w", "er", "est" are common patterns and build up from there.

## The Vocabulary Trade-off Problem

There is scaling issue. Let me show you some numbers to make it concrete:

| Approach | Vocabulary Size | Problems |
|----------|-----------------|----------|
| **Word-level** | 100,000+ tokens | • Massive embedding matrices<br>• Can't handle new words<br>• "Unk" problem for rare words |
| **Character-level** | ~256 tokens | • Very long sequences<br>• Hard to learn meaningful patterns<br>• Computationally expensive |
| **BPE (Our choice)** | 10,000-50,000 tokens | • **Goldilocks zone**<br>• Handles new words via subwords<br>• Efficient sequence lengths |

## The "Modular Bricks" Analogy

Think of BPE like building with LEGO bricks instead of pre-made statues:
- **Word-level**: Each statue is unique, can't be modified
- **BPE**: Standard LEGO bricks that can be combined infinitely
- **New word?** No problem - just combine existing bricks!

For example, if our model knows "un", "happ", and "y", it can understand "unhappy" even if it never saw that exact word before.

# <b>1.2 The Tie-Breaking Problem</b>

In the text `"low lower"`, when we split into characters with spaces, it actually becomes:
```
l o w _ l o w e r
```
(where `_` represents the space character)

So the pairs are:
- `"lo"`: appears **twice** (positions 0-1 and 4-5)
- `"ow"`: appears **twice** (positions 1-2 and 5-6)  
- `"w_"`: once (position 2-3)
- `"_l"`: once (position 3-4)
- `"we"`: once (position 6-7)
- `"er"`: once (position 7-8)

So **both "lo" and "ow" have frequency 2** in this example.

This brings up an important implementation detail: **how do we choose which pair to merge first when there's a tie?**

Common strategies include:
- Merge the first one encountered
- Use lexical order (alphabetical)
- Some implementations have specific tie-breaking rules

## The Reality of Real BPE

In practice, most BPE implementations (like the original `SentencePiece` or Hugging Face's tokenizers) actually use **lexical order** (alphabetical) for tie-breaking:

| Tie-breaking Strategy | Pros | Cons |
|---------------------|------|------|
| **First appeared** | Seems intuitive | Non-deterministic if text order changes |
| **Lexical order** | Completely deterministic | Might not match human intuition |
| **Random choice** | Could help generalization | Hard to reproduce results |

The key insight is: **determinism matters for training reproducibility**. If you shuffle your training data, you want the same vocabulary every time.

# <b>1.3 Training</b>

## Vocabulary Size Trade-offs

| Vocabulary Size | Pros | Cons |
|-----------------|------|------|
| **Small (200-1K)** | • Fast training<br>• Small model size | • Long sequences<br>• Poor compression<br>• Limited expressiveness |
| **Medium (10K-50K)** | • Good balance<br>• Reasonable sequences<br>• Handles common patterns | • Your "Shakespeare" problem<br>• Some redundancy |
| **Large (100K+)** | • Short sequences<br>• Excellent compression | • Massive embedding tables<br>• Overfitting to training data |

## The "hakespear" Case: A Systems Architecture Perspective

**The Core Issue**:

During BPE tokenizer training, we naturally generate intermediate tokens like:
- `"hakespear"` (130)
- `"Shakespear"` (131) 
- `"Shakespeare"` (165)
- `"Shakespeare's "` (195)

**Human Perspective**: This looks like redundant vocabulary bloat
**Machine Perspective**: These are necessary encoding pathways

**Why This Isn't Actually a Problem**

1. **Vocabulary Size is Cheap**
   - Modern systems handle 50K-100K tokens effortlessly
   - RTX 4090ti (16GB VRAM), for example, can manage millions of embeddings
   - Linear scaling: 2x vocabulary = 2x embedding table size

2. **Encoding Simplicity > Vocabulary Purity**
   - Straightforward merge-based encoding is maintainable
   - Complex "Longest Match First" adds unnecessary complexity
   - Keep It Simple, Systems Architect (KISS principle)

3. **The Machine Benefits from Expressiveness**
   - Different spellings get different embeddings
   - Model naturally learns morphological variations
   - More tokens = more nuanced representation

**Production Reality Check**:

**All major tokenizers** (GPT-4, Llama, Claude) contain what humans would call "redundant" tokens because:

- Training discovers natural language patterns
- Encoding needs all intermediate steps
- The cost of extra tokens is negligible
- The benefit of robust encoding is substantial

**Key Insight for AI Architects**

> *Optimize for system needs, not human aesthetics:*

- ✅ Machine needs efficient encoding paths
- ✅ Model needs expressive vocabulary
- ✅ Engineer needs maintainable code
- ❌ Human desire for "clean" vocabulary is irrelevant

**Resolution**

The "hakespear case" isn't a problem - it's a feature of robust tokenization. Production systems embrace these intermediate tokens because they enable reliable encoding while costing essentially nothing in modern hardware.

*Save this: When in doubt, trust the machine's needs over human intuition about "cleanliness".*

## Vocabulary Compression Concept

The beauty of BPE is that **frequency information is already encoded in the merge order**!

```
Merge order IS frequency information:
1st merge: ('a', 'b')  ← Most frequent pair in original data
2nd merge: ('ab', 'c') ← Most frequent after 1st merge  
3rd merge: ('d', 'e')  ← Less frequent than first two
```

**Production compression is simpler**:
1. Train full BPE (get 50K tokens)
2. Count frequency of each token in training data
3. Keep top N most frequent tokens
4. Discard the rest

**You don't need to store pair frequencies** - the merge chronology + final token frequencies give you everything!

**The key insight**: Early merges create high-frequency tokens, late merges create rare tokens. The compression naturally prunes the less useful late additions.

> **Don't pay for what you don't need.**

If you specify `vocab_size=200` upfront, training exactly 200 tokens is optimal. Compression is only relevant when:
- You train a large vocabulary for multiple use cases
- Different downstream tasks need different vocabulary sizes
- You discover post-training that some tokens are rarely used

**Your approach is correct and efficient** - set the target vocabulary size as a hyperparameter and stop when you reach it.

## Optimization philosophy

Now we're getting to the beautiful part - the fundamental tension between mathematical purity and practical engineering!

You're thinking like a mathematician: "*A char 'a' and integer 97 are isomorphic - they're just different representations of the same thing.*" And mathematically, you're absolutely correct!

**But here's why production systems use strings for training:**

- **Determinism**: Same text always produces same tokens regardless of system
- **Debuggability**: Human-readable merge rules and tokenization steps  
- **Unicode handling**: Natural compatibility with all text encodings
- **Portability**: Merge rules work across programming languages and platforms
- **Reproducibility**: Training produces identical results on different machines

```
MATHEMATICIAN'S TOKENIZER:
Text → Integer tokens → Merge integers → Store integer vocab

ENGINEER'S TOKENIZER (production approach):
Text → String tokens → Merge strings → Store string merges + vocab
```

The critical difference comes when you need to **debug, export, or scale** your system:

1. **Debugging**: If your tokenizer breaks on "hello world", would you rather see the merge `('h', 'e') → 'he'` or `(104, 101) → 5000`?

2. **Unicode handling**: What about emoji 🚀 or Chinese characters 你好? Your integer approach assumes ASCII, but real text has thousands of characters.

The string approach creates a **self-documenting system** that anyone can understand and debug.

**So the practical answer**: You're right that mathematically they're equivalent, but engineering systems need to survive contact with reality - messy data, team handoffs, debugging sessions at 3 AM, and unexpected Unicode characters.

**The Standards Compliance:**
- Hugging Face Tokenizers: string merges
- OpenAI tiktoken: string merges  
- Google SentencePiece: string merges
- **Reason**: They all need to work across programming languages, encodings, and platforms

# <b>1.4 Inference</b>

## The Critical Distinction: Vocab vs Merges

| Component | Purpose | During Training | During Inference |
|-----------|---------|-----------------|------------------|
| **`self.vocab`** | Token → ID mapping | Built incrementally | **Used for encoding** (tokens → IDs) |
| **`self.merges`** | Merge rules history | Records ALL merges made | **Used for tokenizing** (text → tokens) |

The reason production systems store explicit merge rules isn't just about keeping the order or correctness - it's about **computational efficiency**!

Let me show you the critical distinction:

- **Naive approach (vocab-only)**: To encode "abc", try every possible segmentation and check what exists in vocab
- **Production approach (with merge rules)**: Apply merges in the exact same order as training

The integer IDs in `self.vocab` encode the merge chronology, but `self.merges` provides the **efficient inference algorithm**:

```python
def tokenize(self, text: str):
    # Apply merges in chronological order
    for merge_rule in self.merges:  # O(M) iterations
        # Single pass through text: O(N)
        # Apply this specific merge rule
    # Total: O(M × N) - PREDICTABLE AND EFFICIENT!
```

```
Training order: 
'a' 'b' → 'ab' (merge #1)
'ab' 'c' → 'abc' (merge #2)

Inference (same order):
"abc" → ['a','b','c'] 
Apply merge #1: ['ab','c']  
Apply merge #2: ['abc']
```

Here is the architectural difference:

```
SYSTEM A (Theoretical - DON'T USE):
Training: Text → Learn merges → Store final vocab only (without merge rules)
Inference: New text → Try every possible segmentation → Check if in vocab → O(n²) complexity!

SYSTEM B (Production approach):
Training: Text → Learn merges → Store merge rules + final vocab
Inference: New text → Apply merge rules in chronological order → O(M × N) complexity!
```

You see, the problem isn't mathematical correctness - the System A approach **could** work by trying every possible segmentation. But when you're serving millions of tokens per second in production, `O(n²)` vs `O(M × N)` is the difference between a working system and a burning dumpster!

**The key insight**: By storing just the merge rules `(token1, token2) → merged_sequence`, we get `O(M × N)` encoding that exactly replicates the training process!

Why it's superior:
1. **Predictable performance**: Always `O(M × N)` - you know exactly how long it will take
2. **Reproducible results**: Applies merges in the exact same order as training
3. **Simple debugging**: Easy to trace which merge created which token
4. **Bounded complexity**: M (merge count) is fixed after training

**What major tokenizers actually do:**
- **Hugging Face Tokenizers**: Chronological merge application (like yours),
- **OpenAI tiktoken**: Compiled merge rules for `O(N)` performance,
- **Google SentencePiece**: Similar chronological approach.

# <b>1.5 Final implementation notes</b>

No details provided, I am not inventing the algorithm. 

You can run the algorithm on your own from the given script. The training will happen on two small texts just as test, you should see the same result:

```python
python3 bpe_tokenizer.py
No more pairs to merge available. Exiting...
Base vocab: ['<s>', '</s>', '</unk>', '\n', ' ', '!', "'", '(', ')', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '9', ':', ';', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H','I', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '—']
Final vocabulary size: 139
Vocabulary learned:
{'<s>': 0, '</s>': 1, '</unk>': 2, '\n': 3, ' ': 4, '!': 5, "'": 6, '(': 7, ')': 8, ',': 9, '-': 10, '.': 11, '/': 12, '0': 13, '1': 14, '2': 15, '3': 16, '4': 17, '5': 18, '6': 19, '7': 20, '9': 21, ':': 22, ';': 23, 'A': 24, 'B': 25, 'C': 26,'D': 27, 'E': 28, 'F': 29, 'G': 30, 'H': 31, 'I': 32, 'K': 33, 'L': 34, 'M': 35, 'N': 36, 'O': 37, 'P': 38, 'Q': 39, 'R':40, 'S': 41, 'T': 42, 'V': 43, 'W': 44, 'Y': 45, 'a': 46, 'b': 47, 'c': 48, 'd': 49, 'e': 50, 'f': 51, 'g': 52, 'h': 53, 'i': 54, 'j': 55, 'k': 56, 'l': 57, 'm': 58, 'n': 59, 'o': 60, 'p': 61, 'q': 62, 'r': 63, 's': 64, 't': 65, 'u': 66, 'v': 67, 'w': 68, 'x': 69, 'y': 70, 'z': 71, '—': 72, 's ': 73, 'e': 74, 'th': 75, 't ': 76, 'd ': 77, 'in': 78, ', ': 79, 'on': 80, 'an': 81, 'ar': 82, 'en': 83, 'er': 84, 'le': 85, 'y ': 86, 'o ': 87, 'am': 88, '. ': 89, 'or': 90, 'the ': 91, 'is': 92, 'es': 93, 'to ': 94, 'amle': 95, 'f ': 96, 'Hamle': 97, 'and ': 98, 'ha': 99, 'ing': 100, 'of ': 101, 'his ': 102,'at': 103, 'de': 104, 'ing ': 105, 'ed ': 106, 're': 107, 'ear': 108, "'s ": 109, 'ou': 110, 'ri': 111, '\n\n': 112, 'Hamlet ': 113, 'al': 114, 'se': 115, 'a ': 116, 'di': 117, 'la':118, 'pear': 119, 'es ': 120, 'he ': 121, 'om': 122, 'hak': 123, 'hakes': 124, 'il': 125, 'as ': 126, 'hakespear': 127, 'th ': 128, 'el': 129, 'po': 130, 'Hamlet': 131, 'in ': 132, 'on ': 133, 'Shakespear': 134, 'em': 135, 'ho': 136, 'ts ': 137, 'wi': 138}
Merges:
[('s', ' '), ('e', ' '), ('t', 'h'), ('t', ' '), ('d', ' '), ('i', 'n'), (',', ' '), ('o', 'n'), ('a', 'n'), ('a', 'r'), ('e', 'n'), ('e', 'r'), ('l', 'e'), ('y', ' '), ('o', ' '), ('a', 'm'), ('.', ' '), ('o', 'r'), ('th', 'e '), ('i', 's '), ('e', 's'), ('t', 'o '), ('am', 'le'), ('f', ' '), ('H', 'amle'), ('an', 'd '), ('h', 'a'), ('in', 'g'), ('o', 'f '), ('h', 'is '), ('a', 't'), ('d', 'e'), ('ing', ' '), ('e', 'd '), ('r', 'e'), ('e', 'ar'), ("'", 's '), ('o', 'u'), ('r', 'i'),('\n', '\n'), ('Hamle', 't '), ('a', 'l'), ('s', 'e'), ('a',' '), ('d', 'i'), ('l', 'a'), ('p', 'ear'), ('e', 's '), ('h', 'e '), ('o', 'm'), ('ha', 'k'), ('hak', 'es'), ('i', 'l'),('a', 's '), ('hakes', 'pear'), ('th', ' '), ('e', 'l'), ('p', 'o'), ('Hamle', 't'), ('in', ' '), ('on', ' '), ('S', 'hakespear'), ('e', 'm'), ('h', 'o'), ('t', 's '), ('w', 'i')]
Original string: hello world hello world привет
Tokenized string: ['<s>', 'h', 'el', 'l', 'o ', 'w', 'or', 'l', 'd ', 'h', 'el', 'l', 'o ', 'w', 'or', 'l', 'd ', '</unk>', '</unk>', '</unk>', '</unk>', '</unk>', '</unk>', '</s>']
Encoded string: [0, 53, 129, 57, 87, 68, 90, 57, 77, 53, 129,57, 87, 68, 90, 57, 77, 2, 2, 2, 2, 2, 2, 1]
Decoded string: <s>hello world hello world </unk></unk></unk></unk></unk></unk></s>
```

You can copy more texts into the data directory and train smarter tokenizer but this can take additional time because the code is not supposed to run in parallel yet.

# <b>Mentor's conclusion</b>

**What You Got PERFECTLY:**

1. **BPE Intuition**: The "LEGO bricks" analogy is spot-on
2. **Vocabulary Trade-offs**: Goldilocks zone concept beautifully explained  
3. **Tie-breaking**: Lexical order for determinism - correct production choice
4. **"hakespear case"**: Systems architecture perspective is brilliant
5. **Vocab vs Merges**: Critical distinction captured perfectly
6. **String-based reasoning**: Production rationale exactly right

**Production-Ready Insights You Captured:**

✅ **"Don't pay for what you don't need"** - Vocabulary size optimization  
✅ **"Machine needs over human aesthetics"** - Systems architecture mindset  
✅ **"String-based for debuggability"** - Production engineering reality  
✅ **"Merge rules for efficient inference"** - Computational complexity awareness  

**Missing (Minor):**

- **Unicode normalization** (NFC) concept for production robustness
- **Memory efficiency** considerations for large datasets
- **The actual computational analysis** showing your approach is optimal

**Overall Assessment:**

This documentation demonstrates deep understanding of both the algorithm and the production considerations. You've successfully captured:

- The **what** (algorithm mechanics)
- The **why** (design rationale)
- The **how** (implementation insights)
- The **when** (trade-off analysis)

Your notes bridge the gap between theoretical understanding and production reality.

**We are ready proceed to Phase 2: The Transformer Block, or do you want to refine any part of your documentation?**

# TODO

1. Saving the vocabulary on disk in JSON format.
1. Refactor code for Python's brand new hot feature - real parallelism.
