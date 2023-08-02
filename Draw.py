import networkx as nx
import matplotlib.pyplot as plt


class GraphVisualization:

    def __init__(self):
        # visual is a list which stores all
        # the set of edges that constitutes a
        # graph
        self.lowvisual = []
        self.highvisual = []
        self.nodes = set()

    # addEdge function inputs the vertices of an
    # edge and appends it to the visual list
    def addLowEdge(self, a, b):
        temp = [a, b]
        self.lowvisual.append(temp)
        self.nodes.add(a)
        self.nodes.add(b)
    def addHighEdge(self, a, b):
        temp = [a, b]
        self.highvisual.append(temp)
        self.nodes.add(a)
        self.nodes.add(b)


    # In visualize function G is an object of
    # class Graph given by networkx G.add_edges_from(visual)
    # creates a graph with a given list
    # nx.draw_networkx(G) - plots the graph
    # plt.show() - displays the graph
    def visualize(self):
        G = nx.DiGraph()
        G.add_edges_from(self.highvisual, color='green')
        print('Solid links', self.highvisual)
        G.add_edges_from(self.lowvisual, color='red')
        print('Dashed links', self.lowvisual)
        nx.draw_networkx(G)
        plt.show()

