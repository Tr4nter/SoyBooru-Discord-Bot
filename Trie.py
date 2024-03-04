import discord
import time

class TrieNode:
    def __init__(self):
        self.children = {}
        self.terminal = False
    

class Trie:
    def __init__(self):
        self.root = TrieNode()

    
    def insert(self, text: str):
        tempRoot = self.root
        for level in range(len(text)):
            if not tempRoot.children.get(text[level]):
                tempRoot.children[text[level]] = TrieNode()
            tempRoot = tempRoot.children[text[level]]
        tempRoot.terminal = True
        
        
    async def _recusive_search(self, beginSearchNode: TrieNode, interaction: discord.Interaction, current: str=""):
        result = []
        if beginSearchNode.terminal: result.append(current)

        if interaction.is_expired() or len(beginSearchNode.children) <= 0: return result
        for char, node in beginSearchNode.children.items():
            if interaction.is_expired(): return result
            result = result+(await self._recusive_search(node, interaction, current+char))
        return result 

            
    async def search_autocompletion(self, key: str, interaction: discord.Interaction):
        lastCharRoot = self.root
        for level in range(len(key)):
            if not lastCharRoot.children.get(key[level]):
                return []

            lastCharRoot = lastCharRoot.children.get(key[level])
        return (await self._recusive_search(lastCharRoot, interaction, key))

