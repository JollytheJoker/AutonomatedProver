# Graph Vergleiche

## Motivation
Wenn wir zwei Graphen miteinander vergleichen, laufen wir gefahr in einen rekursions Error zu laufen. Auch können wir im allgemeinen nicht durch einfache Rekursion zwei von einer Variable abhängige Ausdrücke für die Gewichteten-Kanten miteinander vergleichen. Deshalb nutzen wir einen itterativen reduktions Prozess um das Problem schritweise zu reduzieren.

## Algorithmus am Beispiel der `__eq__` Methode

Wir starten bei einem root_node und vergleichen dessen mathematisches Objekt mit dem anderen. Falls dieser Test funktioniert betrachten wir die ArgumentSlots. Falls er fehlschlägt vergleichen wir direkt das node_object des anwendenden Graphen mit dem mathematischen Objekt des anderen.
Die ArgumentSlots werden wie folgt verglichen
* Man berechen zunächst die Anzahl der Schritte um alle Zyklen des einen ArgumentSlots abzuschließen und auf gleiche weise die des andern. Sind diese identisch können wir weiter vergleichen. Ansosnten sind die graphen ungleich `TODO: nicht ganz richtig; falls ArgumentSlots andere child_nodes am Ende haben als der des anderen sind sie ggf. doch gleich`.
* Nun vergleicht man die jeweils erste Kante der ArgumentSlots miteinander. Ist maximal einer der beiden zyklisch und ist sein Gewicht eine Konstante, so unfoldet man die Graphen einfach weiter; ansonsten sind die Graphen ungleich. Sind beide zyklisch, nutzt man folgenden Algorithmus:
  * Man berechne das kgv der jeweiligen Zykluslängen (geteilt durch das jeweilige Kanten-Gewicht; also genau die Anzahl an Schritten, die es für einen Zyklus braucht). Für diese Anzahl an Schritten (d.h. Anzahl Kanten) vergleicht man nun beide Graphen weiter, sodass man durch das kgv wieder bei dem Ursprungs-Node beider Graphen angekommen ist. Sind die Graphen bis dahin äquivalent, kann man den Vergleich reduzieren.
  * Man berechne die absolute Anzahl an Schritten für beide Graphen brauchen um das Argument des slots vollständig 'abzuarbeiten'. Die Differenz dieser beiden Werte gibt den overhang für das Argument mit mehr Applikationen.
  * Man Restklassenmenge der absoluten Anzahl an Schritten des kleineren Graphen unter modulo betrachtung der Zykluslänge des größeren Graphen. Das sind alle möglichen Indizees, die auf einem Zyklus des größeren Graphen nach Beendigung des kleineren gesamt Zyklus' erreicht werden. Die Berechnung der Restmengenklasse ist einfach nur die Auswertung der Graphen für Werte zwischen 1 bis zum Ziel Modulo. Die meisten standart Operationen sind darunter periodisch.
  * Für jeden Eintrag in der Restklassenmenge berchne nutze man denselben Algorithmus zum Vergleichen, allerdings auf dem nächsten Argument des kleinen Graphen, wobei der root_node des größeren Graphen um den Rest verschoben wird.
