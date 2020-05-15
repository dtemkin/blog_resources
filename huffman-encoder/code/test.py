from huffman import ModifiedHuffmanEncoder

strings = ['how much could a wood chuck',
           'chuck if a wood chuck',
           'could chuck wood?']


enc = ModifiedHuffmanEncoder()
enc.fit(strings)
enc_vals = enc.transform(strings)
print(list(enc_vals))

binenc_vals = ModifiedHuffmanEncoder.convert2binary(enc_vals)
print(binenc_vals)

dec_vals = enc.inverse_transform(enc_vals)
print(list(dec_vals))
