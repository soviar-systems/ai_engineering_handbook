class BPETokenizer:
    """BPETokenizer class definition."""

    # special tokens
    start_string = "<s>"
    end_string = "</s>"
    unknown = "</unk>"

    def __init__(self, special_tokens: tuple = (start_string, end_string, unknown)):
        """Initialize the class entity."""
        self.special_tokens = special_tokens
        # token -> token_id
        self.vocab: dict[str, int] = dict()
        # decoding token_id -> token
        self.reverse_vocab: dict[int, str] = dict()
        self.next_token: int = 0
        # ordered list for storing merging rules ('a', 'c')
        self.merges: list[tuple] = list()
        # base vocab chars for marking unkown chars, see self.vocab
        self.base_vocab: list[str] = list()

    def _initialize_vocab(self, dataset_path):
        """Initialize vocab with individual characters from entire dataset."""
        chars = set()
        for file in dataset_path.iterdir():
            with open(file, "r") as f:
                chars.update(set(f.read()))

        chars = sorted(chars)

        # special tokens first
        for token in self.special_tokens:
            self.vocab[token] = self.next_token
            self.next_token += 1
        self.reverse_vocab = {i: char for char, i in self.vocab.items()}

        # populate vocabs with chars from dataset
        for char in chars:
            self.vocab[char] = self.next_token
            self.reverse_vocab[self.next_token] = char
            self.next_token += 1

        # fix base_vocab for new text tokenization
        self.base_vocab = list(self.vocab.keys())

    def _prepare_dataset(self, dataset_path):
        """Make list of texts broken into single chars."""
        # final list of tokenized texts
        prepaired_dataset = list()

        for file in dataset_path.iterdir():
            with open(file, "r") as f:
                # populate the final list with the new converted line
                prepaired_dataset.append([char for char in f.read()])

        return prepaired_dataset

    def _count_pairs(self, prepaired_dataset: list):
        """Count token pairs across entire dataset."""
        from collections import defaultdict

        # initialize a dictionary for counting occurences
        count_pairs_dict: dict[tuple, int] = defaultdict(int)
        # max_count value
        max_count = 0

        for text in prepaired_dataset:
            for i in range(len(text) - 1):
                pair = (text[i], text[i + 1])
                # update count
                count_pairs_dict[pair] += 1
                # update max_count value
                pair_count = count_pairs_dict[pair]
                if pair_count > max_count:
                    max_count = pair_count

        return max_count, count_pairs_dict

    def _get_merge_candidate(self, max_count: int, count_pairs_dict: dict):
        """Find a new pair for merge."""
        # find most frequent pairs
        popular_pairs = list()
        for pair, count in count_pairs_dict.items():
            # append popular_pairs list
            if count == max_count:
                popular_pairs.append(pair)

        merge_candidate = min(popular_pairs)

        return merge_candidate

    def _append_merges(self, merge_candidate: tuple):
        """Append new rule to self.merges list."""
        self.merges.append(merge_candidate)

    def _update_vocab(self, merge_candidate: tuple):
        """
        Update both vocab and reverse_vocab.

        Parameters
        ----------
        merge_candidate : tuple
          the most popular pair; lexicographically first

        Return
        ------
        merged_string : str

        """
        # convert merge_candidate into char pair
        merged_string = f"{merge_candidate[0]}{merge_candidate[1]}"

        # update vocab with new id-token pair
        self.vocab[merged_string] = self.next_token
        self.reverse_vocab[self.next_token] = merged_string

        self.next_token += 1

        return merged_string

    def _update_prepaired_dataset(
        self, prepaired_dataset: list, merge_candidate: tuple, merged_string: str
    ):
        """
        Update prepaired_dataset with the merged pair.

        Parameters
        ----------
        prepaired_dataset : list
            A list of tokenized texts.
        merge_candidate : tuple
            A pair of tokens to be merged.
        merged_string : str
            A pair of characters from self.vocab.

        """
        # update dataset
        for i in range(len(prepaired_dataset)):
            # original tokenized text
            text = prepaired_dataset[i]
            # updated tokenized text
            updated_text = list()

            # find paired tokens' position and populate new text
            idx = 0
            while idx < len(text):
                if idx == len(text) - 1:
                    updated_text.append(text[idx])
                    break
                if (text[idx], text[idx + 1]) == merge_candidate:
                    updated_text.append(merged_string)
                    # this one is kicked off
                    idx += 1
                else:
                    updated_text.append(text[idx])
                idx += 1

            # update text in dataset
            prepaired_dataset[i] = updated_text

        return prepaired_dataset

    def train(self, dataset: str, vocab_size: int, frequency_threshold: int = 2):
        """
        Convert text to initial tokens.

        The training will stop in one of two scenarios:
        1. The vocab size is reached.
        2. frequency_threshold is reached.

        Parameters
        ----------
        dataset : str
            path to dataset with text stored in regular files.
        vocab_size : int
            desired size of the final vocabulary.
        frequency_threshold : int
            safety measure to avoid rare frequencies to be added to vocab, not including.

        """
        from pathlib import Path

        dataset_path = Path(dataset)

        self._initialize_vocab(dataset_path)

        prepaired_dataset = self._prepare_dataset(dataset_path)

        iter_number = vocab_size - len(self.vocab)
        for _ in range(iter_number):
            # get pairs information
            max_count, count_pairs_dict = self._count_pairs(prepaired_dataset)

            if max_count < frequency_threshold:
                print("No more pairs to merge available. Exiting...")
                break

            # get new candidate pair
            merge_candidate = self._get_merge_candidate(max_count, count_pairs_dict)

            # append the sequence to self.merges
            self._append_merges(merge_candidate)

            # update vocab
            merged_string = self._update_vocab(merge_candidate)

            # merge pair into a new token
            prepaired_dataset = self._update_prepaired_dataset(
                prepaired_dataset, merge_candidate, merged_string
            )

    def tokenize(self, text: str):
        """Encode input string to token_ids."""
        # starting special token
        tokenized_text = [self.start_string]
        # add text as a list of chars
        tokenized_text.extend(list(text))
        # mark the end of tokenized string
        tokenized_text.append(self.end_string)

        # substitute unknown chars to self.unknown
        for i in range(len(tokenized_text)):
            if tokenized_text[i] not in self.base_vocab:
                tokenized_text[i] = self.unknown

        # find pairs
        for i in range(len(self.merges)):
            pair = self.merges[i]
            updated_text = list()
            idx = 0
            while idx < len(tokenized_text):
                if idx == len(tokenized_text) - 1:
                    updated_text.append(tokenized_text[idx])
                    break
                elif pair == (tokenized_text[idx], tokenized_text[idx + 1]):
                    updated_text.append(
                        f"{tokenized_text[idx]}{tokenized_text[idx + 1]}"
                    )
                    idx += 1
                else:
                    updated_text.append(tokenized_text[idx])
                idx += 1
            tokenized_text = updated_text

        return tokenized_text

    def encode(self, tokenized_text: list):
        """Encode tokenized text."""
        encoded_text = list()

        # encode tokens
        for char_seq in tokenized_text:
            try:
                encoded_text.append(self.vocab[char_seq])
            # unknown char
            except Exception:
                encoded_text.append(self.vocab[self.unknown])

        return encoded_text

    def decode(self, encoded_text: list):
        """Decode encoded text back to string."""
        decoded_text = list()

        for token_id in encoded_text:
            decoded_text.append(self.reverse_vocab[token_id])

        return "".join(decoded_text)

    # TODO
    def save(self):
        """Save tokenizer to a JSON file."""
        pass

    # TODO
    def load(self):
        """Load tokenizer from a JSON file on disk."""
        pass
