import time

import bpe_tokenizer


def main():
    """Run the script."""
    start = time.perf_counter()

    dataset_path = "../data/shakespeare_dataset_test"

    my_tokenizer = bpe_tokenizer.BPETokenizer()
    my_tokenizer.train(dataset_path, vocab_size=2000, frequency_threshold=20)

    print("Base vocab:", my_tokenizer.base_vocab)

    print("Final vocabulary size:", len(my_tokenizer.vocab))

    print("Vocabulary learned:")
    print(my_tokenizer.vocab)

    print("Merges:")
    print(my_tokenizer.merges)

    string = "hello world hello world привет"
    result = my_tokenizer.tokenize(string)
    print(f"Original string: {string}")
    print(f"Tokenized string: {result}")

    encoded_string = my_tokenizer.encode(result)
    print("Encoded string:", encoded_string)

    decoded_string = my_tokenizer.decode(encoded_string)
    print("Decoded string:", decoded_string)

    end = time.perf_counter()

    result = end - start
    print(f"Time spent: {result:.6f}")


if __name__ == "__main__":
    main()
