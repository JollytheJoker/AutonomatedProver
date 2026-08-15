import networkx as nx
import matplotlib.pyplot as plt
from ExpressionTree import Node
from CommonStatements import definitions, _attach_at_leaf, ball_func
from MObject import Function, Set, ElementrySet, Variable, Quantor, PowerSet
from pyvis.network import Network
import numpy as np


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
                pass#G.add_edge(A, B, type='contains', color='blue', weight=1.0)

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

            if isinstance(A.math_object, Function):
                bound_set = A.math_object.binding_quantity[1]
            elif isinstance(A.math_object, ElementrySet) or isinstance(A.math_object, Set):
                bound_set = A.math_object
            else:
                bound_set = A.math_object.binding_quantity[0]
            while isinstance(bound_set, PowerSet):
                bound_set = bound_set.binding_quantity[0]
            if bound_set in [nd.math_object for nd in nodes_list]:
                G.add_edge(A, Node(bound_set), type='bound_to', color='red', weight=1.0)


    # 4. Graph visualisieren
    '''plt.figure(figsize=(14, 10))

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
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8)'''

    res = find_best_connectivity_boost_edge(G, nodes_list)

    for key, val in res:
        print(key, val)

    # Legende und Anzeige
    visualize_interactive_concept_graph(G)


def visualize_interactive_concept_graph(G: nx.DiGraph, output_filename="concept_graph.html"):
    """
    Wandelt einen NetworkX DiGraph in eine interaktive PyVis-HTML-Datei um.
    Erlaubt Drag-and-Drop, Zoomen und Physik-Simulation.
    """
    # 1. PyVis-Netzwerk initialisieren (gerichteter Graph)
    net = Network(height="750px", width="100%", directed=True, notebook=False)

    # 2. Physik-Algorithmus aktivieren (Barnes-Hut für automatisches Anordnen)
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=150)

    # 3. Knoten aus NetworkX in PyVis übertragen
    for node in G.nodes():
        # Label und Tooltip generieren
        label_str = G.nodes[node].get('label', str(node))
        net.add_node(
            n_id=str(id(node)),  # Eindeutige ID basierend auf Speicheradresse
            label=label_str,
            title=f"Typ: {type(node.math_object).__name__}\nString: {str(node)}",  # Tooltip beim Hovern
            color="#97C2FC",
            size=25
        )

    # 4. Kanten (Relations) übertragen
    # Hinweis: Da PyVis mit String-IDs arbeitet, mappen wir die Objekte auf ihre IDs
    node_to_id = {node: str(id(node)) for node in G.nodes()}

    for u, v in G.edges():
        edge_data = G[u][v]
        net.add_edge(
            node_to_id[u],
            node_to_id[v],
            label=edge_data.get('type', ''),
            color=edge_data.get('color', 'blue'),
            arrows="to"
        )

    options = """
        {
          "nodes": {
            "font": {
              "color": "white",
              "size": 14,
              "face": "arial"
            }
          },
          "edges": {
            "font": {
              "color": "white",
              "size": 12,
              "align": "middle"
            },
            "smooth": {
              "type": "cubicBezier"
            }
          },
          "physics": {
            "barnesHut": {
              "gravitationalConstant": 0,
              "centralGravity": 0,
              "springLength": 200
            },
            "minVelocity": 0
          }
        }
        """
    net.set_options(options)

    # Optional: Kontroll-Leiste (UI) im Browser anzeigen, um Physik-Parameter anzupassen
    #net.show_buttons(filter_=['physics'])

    # 5. Als HTML speichern und im Standard-Browser öffnen
    net.show(output_filename, notebook=False)
    print(f"Interaktiver Graph erfolgreich gespeichert unter: {output_filename}")


def find_best_connectivity_boost_edge(G: nx.Graph, nodes_list: list):
    """
    Berechnet die Konnektivität für jedes valide Kanten-Paar im Graphen.
    Valide bedeutet: Beide Knoten haben exakt dieselbe binding_quantity.
    """
    n = len(nodes_list)
    idx = {node: i for i, node in enumerate(nodes_list)}

    # 1. Distanzmatrix initialisieren und befüllen (wie in deinem test.py)
    D = np.full((n, n), np.inf)
    for u, lengths in nx.all_pairs_shortest_path_length(G):
        if u in idx:  # Sicherstellen, dass u in unserer Liste ist
            i = idx[u]
            for v, d in lengths.items():
                if v in idx:
                    j = idx[v]
                    D[i, j] = d

    # 2. Helfer-Funktion für die Matrix-Operation
    def calc_connectivity(idxA, idxB):
        # Broadcasting Magie zur Distanz-Aktualisierung
        distancesToA = D[:, idxA][:, None]
        distancesToB = D[:, idxB][:, None]
        distancesFromA = D[idxA, :][None, :]
        distancesFromB = D[idxB, :][None, :]

        via_ab = distancesToA + 1 + distancesFromB
        via_ba = distancesToB + 1 + distancesFromA

        newD = np.minimum(D, np.minimum(via_ab, via_ba))
        return np.sum(np.where(newD > 1e-7, 1 / newD, 0))

    results = {}

    # 3. Brute-Force über alle möglichen Knotenpaare
    for u in nodes_list:
        for v in nodes_list:
            # Gleicher Knoten oder Kante existiert bereits -> überspringen
            if u == v or G.has_edge(u, v) or G.has_edge(v, u):
                continue

            '''if isinstance(u.node_object, Function) or isinstance(v.node_object, Function) or isinstance(u.node_object, Variable) or isinstance(v.node_object, Variable):
                continue'''

            # --- VALIDIERUNG DER BINDING QUANTITY ---
            # Wir prüfen, ob beide Knoten das Attribut haben und ob es identisch ist
            if not hasattr(u.math_object, 'binding_quantity') or not hasattr(v.math_object, 'binding_quantity'):
                continue

            if u.child_nodes:
                u_obj = u.node_object
            else:
                u_obj = u.math_object
            u_binding = u_obj.binding_quantity[1] if isinstance(u_obj, Function) else (u_obj if isinstance(u_obj, ElementrySet) else u_obj.binding_quantity[0])
            if v.child_nodes:
                v_obj = v.node_object
            else:
                v_obj = v.math_object
            v_binding = v_obj.binding_quantity[1] if isinstance(v_obj, Function) else (v_obj if isinstance(v_obj, ElementrySet) else v_obj.binding_quantity[0])
            if v_binding != u_binding:
                continue
            # ----------------------------------------

            # 4. Konnektivitäts-Boost berechnen und speichern
            boost = calc_connectivity(idx[u], idx[v])
            results[(u, v)] = boost

    # 5. Ergebnisse absteigend sortieren (Höchster Boost zuerst)
    sorted_results = {k : v for k, v in sorted(results.items(), key=lambda item: item[1], reverse=True)}

    return sorted_results

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
nodes.append(Node(X))
nodes.append(Node(Y))

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

build_and_visualize_concept_graph(nodes)
