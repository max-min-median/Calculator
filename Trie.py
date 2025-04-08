import heapq

class Trie:

    def __init__(self, key, children=None):
        self.key = key
        self.children = [] if children is None else children

    def __repr__(self): return f"'{self.key}'"

    def insert(self, word):
        if word == '':
            if self.children[0:1] != [Trie.TERMINAL]: self.children[0:0] = [Trie.TERMINAL]
            return
        idx, foundChild = self.findChildIndex(word[0])
        if not foundChild:
            self.children[idx:idx] = [Trie(word, [Trie.TERMINAL])]
        else:
            longestPrefix = 0
            childWord = self.children[idx].key
            for letter in childWord:
                if letter != word[longestPrefix:longestPrefix + 1]: break
                longestPrefix += 1
            if longestPrefix < len(childWord):  # split child
                self.children[idx].key = childWord[longestPrefix:]
                self.children[idx] = Trie(childWord[:longestPrefix], [self.children[idx]])
                self.children[idx].insert(word[longestPrefix:])
            else:
                self.children[idx].insert(word[longestPrefix:])

    def delete(self, word):
        """
        Procedure for deletion:
        - find node and delete TrieNode.TERMINAL (should be the first child)
        - if this node then has exactly one (non-TERMINAL) child, then we merge it with its child:
           - take over its child's children.
           - concatenate its key with its child's key
        - else if this node then has no more children, then we delete it (remove from parent's list of children).
           - now we must check if the parent has exactly one non-TERMINAL child, as above.
        """
        seq, foundWord = self.find(word)
        if not foundWord: raise Exception(f'Trie does not contain "{word}"!')
        seq[0].children[0:1] = []
        if len(seq[0].children) == 1: seq[0]._mergeWithChild()
        elif len(seq[0].children) == 0:
            parent = seq[1]
            idx, foundChild = parent.findChildIndex(seq[0].key[0])
            if not foundChild: raise Exception('delete(): parent could not find child')
            parent.children[idx:idx+1] = []
            if len(parent.children) == 1: parent._mergeWithChild()

    def _mergeWithChild(self):
        if self.children[0] == Trie.TERMINAL: return
        self.key += self.children[0].key
        self.children = self.children[0].children

    def findChildIndex(self, letter):
        L, R, children = 0, len(self.children), self.children
        while L < R:
            M = (L + R) // 2
            keyFirstLetter = children[M].key[0:1]
            if keyFirstLetter == letter: return M, True
            elif keyFirstLetter < letter: L = M + 1
            else: R = M
        return L, False

    def find(self, word):
        """
        Attempts to search for `word` in the trie.
        Returns a tuple `(seq, result)`, where `seq` is the sequence of nodes visited during the search, and `result`
        is one of:
        - `True`: `word` is a valid word.
        - `False`: `word` is not a valid word, but prefixes one or more valid words.
        - `None`: `word` is neither a valid word, nor a valid prefix.
        """
        if word == '': return [self], self.children[0] == Trie.TERMINAL
        idx, foundChild = self.findChildIndex(word[0])
        if not foundChild: return [self], None
        childWord = self.children[idx].key
        if word.startswith(childWord):
            seq, result = self.children[idx].find(word[len(childWord):])
            seq.append(self)
            return seq, result
        elif childWord.startswith(word):
            return [self.children[idx], self], False
        else:
            return [self], None

    def nearestAutocomplete(self, prefix, n=10):
        """
        Returns up to `n` "nearest" valid words from `prefix`, including `prefix` itself if it is a valid word.
        A word is "nearer" if it is shorter, with ties broken by lexicographical order.
        Uses Dijkstra's algorithm.
        """
        seq, result = self.find(prefix)
        if result is None: return []  # None indicates no words with this prefix.
        
        nearestPrefix = ''.join(elem.key for elem in reversed(seq))
        minPQ = [(0, nearestPrefix, seq[0])]
        matches = []
        while len(minPQ) > 0 and len(matches) < n:
            dist, prefixStr, node = heapq.heappop(minPQ)
            for child in node.children:
                if child == Trie.TERMINAL:
                    matches.append(prefixStr)
                else:
                    heapq.heappush(minPQ, (dist + len(child.key), prefixStr + child.key, child))
        return matches
    
    def numNodes(self):
        count = 1  # self
        for child in self.children:
            if child == Trie.TERMINAL: continue
            count += child.numNodes()
        return count


    def numChars(self):
        count = len(self.key)  # self
        for child in self.children:
            if child == Trie.TERMINAL: continue
            count += child.numChars()
        return count


    def numWords(self):
        count = 0
        for child in self.children:
            if child == Trie.TERMINAL: count += 1
            else: count += child.numWords()
        return count


    def printWords(self, prefix=''):
        newPrefix = prefix + self.key
        for child in self.children:
            if child == Trie.TERMINAL:
                print(newPrefix)
            else:
                child.printWords(newPrefix)

    def printTrie(self, spaces=0, root=True):
        if self == Trie.TERMINAL: return
        firstChild = True
        for ch in self.children:
            if ch == Trie.TERMINAL: continue
            if not firstChild:
                print()
                print(' ' * spaces, end='')
            firstChild = False
            s = ('' if root else ' -> ') + ch.key + ('.' if ch.children[0] == Trie.TERMINAL else '')
            print(s, end='')
            ch.printTrie(spaces + len(s), False)
        if root: print()

    @staticmethod
    def fromTextFile(file):
        Trie.TERMINAL = Trie('')
        root = Trie('')
        with open(file) as f:
            while (word := f.readline().strip()):
                # if "'" in word: continue
                root.insert(word)
        return root

    @staticmethod
    def fromCollection(words):
        Trie.TERMINAL = Trie('')
        root = Trie('')
        for word in words:
            root.insert(word)
        return root


Trie.TERMINAL = Trie('')

if __name__ == '__main__':
    trie = Trie.fromTextFile('large_dict.txt')
    # print(trie.find('zebra'))
    # print(trie.find('knight'))
    # print(trie.find('colossus'))
    # print(trie.find('pli'))
    # print(trie.find('chromhtr'))
    # print(trie.find('chh'))
    # print(trie.find('childre'))
    print(trie.find('drearin'))
    # trie.printWords()
    # print()
    # trie.printTrie()
    # trie.insert('rubix')
    # trie.printTrie()
    # trie.delete('rubicon')
    # trie.delete('ruber')
    # trie.printTrie()
    print(trie.nearestAutocomplete('abcd'))
    ...