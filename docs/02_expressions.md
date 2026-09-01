# 02. Terme

## 1. Motivation
Um komplexere Eigenschaften und Konkatenationen dargestellt zu können, müssen wir Objekte verknüpfen können.

## 2. Typisierung
Wir nutzen dafür gerichtete, zyklische Graphen. Knoten halten mathematische Objekte, sowie ArgumentSlots. Jeder ArgumentSlot hält eine beliebiege Menge geordneter gewichteter Kanten. Gewichte dienen der Rekurrsion und können nur dann größer (bzw. ungleich 1) sein, falls sie einen Zyklus auf diesem Graphen bilden, d.h. ihr jeweiliger parent_node selbst wieder auf einem Pfad, nutzend dieser Knate liegt. Gewichte können positive ganze Zahlen, unendlich oder selbst wieder Ausdrucksgraphen sein (diese müssen dann jedoch immer einen positivein, ganzzahligen Ausdruck liefern). Das Gewicht gibt an, wie oft man von einem Knoten aus diese Kante auf einem Pfad geht, bevor man die im ArgumentSlot nächste Kante nutzt.  

## 3. Implementierungsübersicht
In der Umsetzung wird der Graph durch drei Datenstrukturen repräsentiert, um die in Kapitel 2 definierte Typisierung darzusetellen:
1. **Node (Knoten):** Hält ein mathemtisches Objekt (das 5-Tupel), ein Tupel an ArgumentSlots und eine is_root_node Flagge. 
2. **ArgumentSlot:** Repräsentiert die Parameter-Position von einem Objekt (also den Input einer Funktion). Er hält ein geordnetes Tupel von Edge-Objekten.
3. **Edge (Kante):** Verbindet zwei Nodes gerichtet miteinander und besitzt ein weight (Gewicht). Das Gewicht ist standardmäßig 1, kann aber bei Zyklen eine natürliche Zahl, unendlich ($\infty$) oder einen anderen Graphen (der eine natürliche Zahl evaluiert) sein.

## 4. Beispiele

**Beispiel 4.1: Azyklischer Graph (Standard-Baum)**
Der Ausdruck $f(B_{\epsilon}^{d_x}(x_0))$ wird topologisch wie folgt aufgebaut:
* **Knoten 1 ($f$):** is_root_node=True. Besitzt genau einen ArgumentSlot.
  * Dieser Slot hält eine einzelne Kante (weight=1) und zeigt auf Knoten 2.
* **Knoten 2 ($B$):** Repräsentiert den Ball. Besitzt drei ArgumentSlots.
  * Slot 1 hält eine Kante (weight=1) zu Knoten 3 ($d_x$).
  * Slot 2 hält eine Kante (weight=1) zu Knoten 4 ($\epsilon$).
  * Slot 3 hält eine Kante (weight=1) zu Knoten 5 ($x_0$).
* **Knoten 3, 4, 5:** Sind Blatt-Knoten ohne eigene ArgumentSlots (ihr mathematische Objekt muss vom Typ Menge sein).

**Beispiel 4.2: Zyklischer Graph**
Wir betrachten die 5-fache Anwendung einer Nachfolgerfunktion $S^5(0)$:
* **Knoten 1 ($S$):** is_root_node=True. Besitzt einen ArgumentSlot.
  * Dieser Slot hält zwei Kanten in folgender Reihenfolge:
    1. Eine Kante zurück zu sich selbst, mit weight=4 (Zyklus-Definition).
    2. Eine Kante zu Knoten 2 mit weight=1.
* **Knoten 2 ($0$):** Blatt-Knoten.

Zu lesen: Gehe von S viermal die erste Kante im Slot im Kreis, beim fünften Mal nimm die nächste Kante zu 0.