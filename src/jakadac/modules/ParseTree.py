class ParseTreeNode:
    def __init__(self, name, token=None):
        self.name = name          # Name of the nonterminal or token
        self.token = token        # Associated token for terminal nodes
        self.children = []        # List of child nodes

    def add_child(self, child):
        self.children.append(child)

    def __str__(self):
        if self.token:
            return f"{self.name} -> {self.token.lexeme}"
        return self.name

    def __repr__(self):
        return str(self)

class ParseTree:
    def __init__(self):
        self.root = None

class ParseTreePrinter:
    def print_tree(self, node, indent=0):
        print("  " * indent + str(node))
        for child in node.children:
            self.print_tree(child, indent + 1)
