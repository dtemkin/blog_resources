from receipts.enc import BaseEncoder
from receipts import ENCODERS_DIR

import heapq
import os
import csv
from collections import Counter
from string import ascii_lowercase, digits, punctuation
import numpy as np


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

        return (self.freq < other.freq)

    def __eq__(self, other):
        if other is None:
            return -1
        if not isinstance(other, HeapNode):
            return -1

        return (self.freq == other.freq)

    def __gt__(self, other):

        if other is None:
            return -1
        if not isinstance(other, HeapNode):
            return -1

        return (self.freq > other.freq)


class FileUtils:
    f = os.path.join(ENCODERS_DIR, 'labelled_enc_huffman.csv')

    @classmethod
    def dump(cls, data, *args, **kwargs):
        ow = kwargs.get('overwrite', False)
        if ow:
            stream = open(cls.f, mode='w')
        else:
            stream = open(cls.f, mode='a')
        writr = csv.writer(stream)
        writr.writerows(["|".join(i) for i in data])
        stream.flush()
        stream.close()

    @classmethod
    def load(cls):
        stream = open(cls.f, mode='r')
        readr = csv.reader(stream)
        stream.close()
        return readr


class Encoder(BaseEncoder):
    def __init__(self):
        super().__init__()
        self.heap = []
        self.mx_string = 0
        self._encoded_training = []
        self.padding_arr = []
    # functions for compression:

    def frequencies(self, strings):
        count = Counter()
        all_strings = list(ascii_lowercase+digits+punctuation)
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
            merged.left, merged.right  = node1, node2
            heapq.heappush(self.heap, merged)

    def make_codes_helper(self, root, current_code):
        if root is None:
            return None

        if root.char is not None:
            self._map[root.char] = current_code
            self._inv_map[current_code] = root.char
            return None

        self.make_codes_helper(root.left, current_code + "0")
        self.make_codes_helper(root.right, current_code + "1")

    def make_codes(self):
        root = heapq.heappop(self.heap)
        current_code = ""
        self.make_codes_helper(root, current_code)

    def _encode(self, strings):
        encoded_text = [self._map[character] for character in strings]
        return encoded_text

    def transform(self, data, *args, **kwargs):
        out = kwargs.get("out", int)
        oper = kwargs.get("oper", 'testing')
        items = []
        _encoded_test = []
        if oper == 'training':
            for e in self._encoded_training:
                string = "".join(e)
                string_pad_size = self.mx_string - len(string)
                
                int_arr = [int(x) for x in 
                           list(string)+self.padding_arr[:string_pad_size]]
                items.append(np.asarray(int_arr))
        else:
            for d in data:
                chars = list(d)
                enc_text = self._encode(chars)
                string = "".join(enc_text)
                if len("".join(enc_text)) > self.mx_string:
                    pass
                else:
                    _encoded_test.append(enc_text)
                    
                    string_pad_size = self.mx_string - len(string)
                    int_arr = [int(x) for x in 
                               list(string)+self.padding_arr[:string_pad_size]]
                    items.append(np.asarray(int_arr))
                    
        return np.matrix(items)

    def generate_padding(self, pad_size, pad_value='9'):
        if pad_size == 'auto':
            pad_size = 0
        elif type(pad_size) is int:
            pad_size = pad_size

        padding = [str(pad_value) for i in range(pad_size)]
        return padding

    def fit(self, data, *args, **kwargs):
        pad_value = kwargs.get("pad_value", '9')
        add_pad = kwargs.get("addtl_pad", 20)
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
            self._encoded_training.append(enc_text)
            if len("".join(enc_text)) > self.mx_string + add_pad:
                self.mx_string = len("".join(enc_text)) + add_pad
        self.padding_arr = self.generate_padding(pad_size=self.mx_string,
                                                 pad_value=pad_value)

    def remove_padding(self, encoded_text):
        encoded_text = encoded_text[:len(encoded_text)-self.mx_string]

        return encoded_text

    def inverse_transform(self, enc_data, *args, **kwargs):
        pass

    def fit_transform(self, data, *args, **kwargs):
        self.fit(data)
        return self.transform(data, oper='training')
