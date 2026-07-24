# 01. Grammatik und Syntax

## 1. Motivation
Um komplexere Eigenschaften und Konkatenationen dargestellt zu können, müssen wir Objekte verknüpfen können.

## 2. Typisierung
Wir nutzen dafür expression trees, als gerichtete graphen. Knoten sind mathematische Objekte und Kanten bilden die Anwendung von Funktionen auf andere Objekte (hierbei zeigt die Richtung immer von der Funktion weg).
Funktionen bilden dabei genau so viele Kanten aus, wie diese parameter in ihrer Bindungsbedingung im input haben.

## 3. Übersicht der mathematischen Objekte
In der Implementierung nutzen wir eine Node-Klassen-Struktur, welche ein mathematisches Objekt, child-nodes und den boolschen Wert is_root_node halten.   

## 4. Beispiel
Der Ausdruck $f(B_{\epsilon}^{d_x}(x_0))$ wird als folgender Baum dargestellt:

> f als root_node <br>
> B ist child_node von f <br>
> $d_x$, $\epsilon$, $x_0$ sind jeweils child_nodes von B und haben keine weiteren Kanten  
   
