import heapq
from collections import Counter
from string import ascii_lowercase, digits, punctuation


class HeapNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        if other is None:
            return -1
        if not isinstance(other, HeapNode):
            return -1

        return self.freq < other.freq

    def __eq__(self, other):
        if other is None:
            return -1
        if not isinstance(other, HeapNode):
            return -1

        return self.freq == other.freq

    def __gt__(self, other):
        if other is None:
            return -1
        if not isinstance(other, HeapNode):
            return -1
        return self.freq > other.freq


class ModifiedHuffmanEncoder:
    def __init__(self):
        super().__init__()
        self.heap = []
        self.mx_string = 0
        self._map, self._inv_map = {}, {}

    # functions for compression:
    @staticmethod
    def frequencies(strings):
        count = Counter()
        all_strings = list(ascii_lowercase + digits + punctuation)
        count.update(all_strings)
        if type(strings) is list:
            for s in strings:
                chars = list(s)
                count.update(chars)

            return count
        elif type(strings) is str:
            chars = list(strings)
            count.update(chars)
            return count
        else:
            raise TypeError("Invalid 'strings' value")

    def make_heap(self, frequency):
        for key in frequency:
            node1 = HeapNode(key, frequency[key])
            heapq.heappush(self.heap, node1)

    def merge_nodes(self):
        while len(self.heap) > 1:
            node1 = heapq.heappop(self.heap)
            node2 = heapq.heappop(self.heap)

            merged = HeapNode(None, node1.freq + node2.freq)
            merged.left, merged.right = node1, node2
            heapq.heappush(self.heap, merged)

    def make_codes_helper(self, root, current_code):
        if root is None:
            return

        if root.char is not None:
            self._map[root.char] = current_code
            self._inv_map[current_code] = root.char
            return

        self.make_codes_helper(root.left, current_code + "0")
        self.make_codes_helper(root.right, current_code + "1")

    def make_codes(self):
        root = heapq.heappop(self.heap)
        current_code = ""
        self.make_codes_helper(root, current_code)

    def _encode(self, strings):
        encoded_text = [self._map[character] for character in strings]
        return encoded_text

    def _decode(self, arr):
        decoded_text = [self._inv_map[character] for character in arr]
        return "".join(decoded_text)

    @staticmethod
    def _generate_padding__(pad_size, pad_value='9'):
        if pad_size == 'auto':
            pad_size = 0
        elif type(pad_size) is int:
            pad_size = pad_size

        padding = "".join([str(pad_value) for i in range(pad_size)])
        return padding

    @staticmethod
    def _remove_padding__(encoded_array):
        return encoded_array[:-1]

    def fit(self, data, *args, **kwargs):
        if type(data) is list:
            text = [t.strip() for t in data]
        else:
            text = data.strip()

        frequency = self.frequencies(text)
        self.make_heap(frequency)
        self.merge_nodes()
        self.make_codes()

        for t in text:
            chars = list(t)
            enc_text = self._encode(chars)
            if len("".join(enc_text)) > self.mx_string:
                self.mx_string = len("".join(enc_text))

    def transform(self, data, *args, **kwargs):
        encoded = []
        for d in data:
            chars = list(d)
            enc_text = self._encode(chars)
            enc_string = "".join(enc_text)
            if len(enc_string) > self.mx_string:
                pass
            else:
                padding = ModifiedHuffmanEncoder._generate_padding__(pad_size=self.mx_string - len(enc_string),
                                                                     pad_value=kwargs.get("pad_value", '9'))
                if padding == "":
                    pass
                else:
                    enc_text.append(padding)
                encoded.append(enc_text)
        return encoded

    def inverse_transform(self, enc_data, *args, **kwargs):
        has_pad = kwargs.get("has_pad", True)

        for row in enc_data:
            enc_row = (ModifiedHuffmanEncoder._remove_padding__(row) if
                       has_pad else row)
            yield self._decode(enc_row)

    def fit_transform(self, data, *args, **kwargs):
        self.fit(data)
        return self.transform(data)

    @classmethod
    def convert2binary(cls, arr):
        new_arr = []
        for x in arr:
            items = []
            for itm in x:
                items.extend(list([int(i) for i in itm]))

            new_arr.append(items)
        return new_arr
