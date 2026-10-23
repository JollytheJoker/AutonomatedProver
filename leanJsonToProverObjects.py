import json


def pretty_print_expr(node, indent=0):
    """
    Druckt einen Lean.Expr-Knoten als hübschen Baum aus.
    """
    prefix = "  " * indent
    node_type = node.get("type")

    if node_type == "const":
        print(f"{prefix}└─ [Const] {node['name']}")
    elif node_type == "bvar":
        print(f"{prefix}└─ [BoundVar] Index: {node['index']}")
    elif node_type == "app":
        print(f"{prefix}└─ [App] (Funktionsanwendung)")
        print(f"{prefix}   ├─ Function:")
        pretty_print_expr(node["fn"], indent + 2)
        print(f"{prefix}   └─ Argument:")
        pretty_print_expr(node["arg"], indent + 2)
    elif node_type == "forallE":
        print(f"{prefix}└─ [Forall / Allquantor] Variable: '{node.get('var')}'")
        print(f"{prefix}   ├─ Domain (Typ):")
        pretty_print_expr(node["domain"], indent + 2)
        print(f"{prefix}   └─ Body (Rumpf):")
        pretty_print_expr(node["body"], indent + 2)
    elif node_type == "sort":
        print(f"{prefix}└─ [Sort] (Universum / Typ von Typen)")
    else:
        print(f"{prefix}└─ [{node_type}]")


suchbegriff = "real"  # Du kannst hier jeden Namen einsetzen
gefunden = False

with open("mathlib_database/mathlib_dump.jsonl", "r", encoding="utf-8") as f:
    for zeile in f:
        eintrag = json.loads(zeile)

        if suchbegriff in eintrag["name"].lower():
            print(f"=== Treffer: {eintrag['name']} ===\n")
            # Wir drucken den Baum des Typs aus
            pretty_print_expr(eintrag["type"])
            gefunden = True
            break  # Wir stoppen beim ersten Treffer, damit es übersichtlich bleibt

if not gefunden:
    print("Nichts gefunden.")