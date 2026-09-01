# 03. Aussagen

## 1. Motivation
Um nicht nur Terme darstellen zu können, sondern auch deren Beziehung, sowie Aussagen der Logik zu treffen, nutzen wir eine auf dem Ausdrucksgraphen aufbauenden AST.

## 2. Definition
Ein solcher AST ist ein Baum, dessen Knoten eine node_function, also logischen Operator (wie $\lor, \land$), Relation (wie $\subseteq, \le$), Node (also Ausdrucksgraphen), boolschen Wert ($\top, \bot$) oder eine allgemeines MetaObjekt (Platzhalter für beliebige andere Objekte des dem MetaObjekt übergebenen Typen) halten. Ein solcher Node hat zwei child_nodes, die entweder selbst wieder ein solches Statement (Aussage) oder None (kein child_node) sind. Für die child_nodes müssen weitere Bedingungen gelte, wie z.B., dass ein node mit Ausdrucksgraphen, keine child_nodes haben darf.

## 4. Beispiel
Die Aussage $A \subseteq B \land B \subseteq C$ wäre als folgender AST strukturiert:
* **Rootnode (LogicalOperation):** Hält die logisch Und-Verknüfung $\land$
  * **Linkte Teilbaum (Relation):** Hält die Teilmengen-Relation $\subseteq$
    * **Linkes Blatt (Node):** Hält den Ausdrucksgraphen für $A$
    * **Rechtes Blatt (Node):** Hält den Ausdrucksgraphen für $B$
  * **Rechter Teilbaum (Relation):** Hält die Teilmengen-Relation $\subseteq$
    * **Linkes Blatt (Node):** Hält den Ausdrucksgraphen für $B$
    * **Rechtes Blatt (Node):** Hält den Ausdrucksgraphen für $C$
