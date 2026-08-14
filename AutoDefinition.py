import networkx as nx
import matplotlib.pyplot as plt
from ExpressionTree import Node
from CommonStatements import definitions, _attach_at_leaf, ball_func
from MObject import Function, Set, ElementrySet, Variable, Quantor


def build_and_visualize_concept_graph(nodes_list: list['Node']):
    """
    Baut den Makro-Graphen aus einer Liste von Nodes auf und visualisiert ihn.
    Prüft dabei auf Teilstrukturen (contains) und Unifikation (mapping).
    """
    # 1. Graphen initialisieren
    G = nx.DiGraph()

    # 2. Alle Nodes als Knoten hinzufügen
    for node in nodes_list:
        G.add_node(node, label=str(node))

    # 3. Kanten (Relations) generieren
    for A in nodes_list:
        for B in nodes_list:
            if A is B:
                continue

            # --- RELATION 1: Teilstruktur (Sub-Concept) ---
            # Prüfen, ob Knoten A strukturell in Knoten B enthalten ist.
            # Da primitive_contains ein Generator ist, prüfen wir, ob er Werte liefert.
            contains_generator = B.primitive_contains(A)
            is_contained = any(True for _ in contains_generator)

            if is_contained:
                # A ist ein Teil von B -> gerichtete Kante von A nach B
                G.add_edge(A, B, type='contains', color='blue', weight=1.0)

            # --- RELATION 2: Mapping / Unifikation ---
            # Prüfen, ob Knoten A in Knoten B umgewandelt werden kann
            mapping, is_possible = A.get_mappings_dict_for_replacement(B)

            if is_possible:
                # A lässt sich auf B mappen -> gerichtete Kante
                # Falls schon eine Kante existiert, updaten wir sie (oder lassen sie separat)
                if G.has_edge(A, B):
                    G[A][B]['type'] += ' & maps_to'
                    G[A][B]['color'] = 'purple'  # Mischung aus beiden
                else:
                    G.add_edge(A, B, type='maps_to', color='green', weight=1.0)

    # 4. Graph visualisieren
    plt.figure(figsize=(14, 10))

    # Automatisches Layout (Spring-Layout zieht verbundene Knoten zusammen)
    pos = nx.spring_layout(G, seed=42, k=0.5)

    # Attribute extrahieren
    labels = nx.get_node_attributes(G, 'label')
    edge_colors = [G[u][v]['color'] for u, v in G.edges()]
    edge_labels = {(u, v): G[u][v]['type'] for u, v in G.edges()}

    # Knoten zeichnen
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2500, alpha=0.9)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_weight='bold')

    # Kanten zeichnen
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, arrowsize=20, node_size=2500)

    # Kanten-Beschriftung (Warum existiert die Kante?)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8)

    # Legende und Anzeige
    plt.title("Automated Concept Graph (AST Nodes)", fontsize=16)
    plt.plot([], [], color='blue', label='Contains (Teilstruktur)')
    plt.plot([], [], color='green', label='Maps to (Unifikation / Typ-Hierarchie)')
    plt.plot([], [], color='purple', label='Contains & Maps To')
    plt.legend(loc='upper left')
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# ==========================================
# Beispiel für den Aufruf (Mock-Setup):
# nodes_list = [node_x, node_y, node_f_x, node_f_B_x, ...]
# build_and_visualize_concept_graph(nodes_list)
# ==========================================
nodes = []

# 1. Basis-Räume (Sets)
X = ElementrySet(quantor=Quantor.DEFINE, association='X')
Y = ElementrySet(quantor=Quantor.DEFINE, association='Y')

definitions['X'] = X
definitions['Y'] = Y

# 2. Metriken
d_X = Function(quantor=Quantor.DEFINE,
               binding_quantity=(Set(quantor=Quantor.FORALL, binding_quantity=(X, X)), definitions["reels"]),
               association='d_X')
d_Y = Function(quantor=Quantor.DEFINE,
               binding_quantity=(Set(quantor=Quantor.FORALL, binding_quantity=(Y, Y)), definitions["reels"]),
               association='d_Y')

# 3. Hauptfunktion f: X -> Y
f = Function(quantor=Quantor.DEFINE, binding_quantity=(X, Y), association='f')

# 4. Variablen (Punkte und Radien)
x = Variable(quantor=Quantor.FORALL, binding_quantity=(X,), association='x')
epsilon = Variable(quantor=Quantor.FORALL, binding_quantity=(definitions['reels'],), association='eps')
delta = Variable(quantor=Quantor.FORALL, binding_quantity=(definitions['reels'],), association='delta')

# 5. Basis-Knoten (Blätter / Leaves)
node_f = Node(f)
node_x = Node(x)
node_d_X = Node(d_X)
node_d_Y = Node(d_Y)
node_eps = Node(epsilon)
node_delta = Node(delta)

nodes.extend([node_f, node_x, node_d_X, node_d_Y, node_eps, node_delta])

# 6. Ball-Funktionen
B_X = ball_func(X)
B_Y = ball_func(Y)

# 7. Komplexe Ausdrücke im strikten Format: child_nodes=[[(node, weight), ...]]

# f(x): 1 Argument -> Kette der Länge 1
node_f_x = Node(f, child_nodes=[[(node_x, 1)]])
nodes.append(node_f_x)

# B_X(d_X, delta, x): 3 Argumente (Metrik, Radius, Punkt)
node_ball_x = Node(B_X, child_nodes=[[(node_d_X, 1)], [(node_delta, 1)], [(node_x, 1)]])
nodes.append(node_ball_x)

# f(B_X(...)): Anwendung von f auf die Delta-Kugel
node_f_ball_x = _attach_at_leaf(node_f, node_ball_x)
nodes.append(node_f_ball_x)

# B_Y(d_Y, eps, f(x)): Epsilon-Kugel um f(x) im Raum Y
node_ball_fx = Node(B_Y, child_nodes=[[(node_d_Y, 1)], [(node_eps, 1)], [(node_f_x, 1)]])
nodes.append(node_ball_fx)

