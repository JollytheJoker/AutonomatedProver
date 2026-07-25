# 03. Aussagen

## 1. Motivation
Wir wollen unsere Terme untereinander in verbindung bringen. Dafür benötigen wir Relationen (wie Teilmenge, kleiner gleich etc.). Zwischen solchen Aussagen können wir anwendungen definieren, um diese zu verknüpfen
## 2. Formale Definition
> **Definition (Aussage)** <br>
> Eine Aussage ist ein Tuple $(T_1, R, T_2)$, wobei $T_1,T_2$ jeweils Terme sind, diese werden durch eine Relation $R$ verbunden. Diese Relation muss Transitiv sein, d.h. $aRb \land bRc \implies aRc$

> **Definition (Anwendung)** <br>
> Sei $A=(T_1,R,T_2)$ eine Aussage und $T_S$ ein Term. Dann ist $A(T_S)$ definert als das Ersetzen des premitiv-äquivalenten Teilbaums $T_1$ in $T_S$ durch $T_2$ unter Ersetzen der Objekte von $T_2$ durch die analogen Objekte im Teilbaum von $T_S$.  

## 3. Implementierung
Wir definieren einfach eine Aussagen Klasse, welche solche zwei terme und relation hält. Eine Anwendung implentieren durch das Ersetzen der Variablen rekusiv. Dabei müssen nun auch Äquivalenz der Quatoren und mathematischen Bedingungen geprüft werden.

## 4. Beispiel
Nun können wir Stetigkeit als einfach Aussage über Bälle definieren. Seien $(X,d_x),(Y,d_y)$ metr. Räume, dann ist $f:X\rightarrow Y$ genau dann stetig wenn <br> 
$\forall x \in X, \epsilon \in \mathbb{R}:\exists\delta\in\mathbb{R}: f(B_{\delta}^{d_x}(x)) \subseteq B_{\epsilon}^{d_y}(f(x))$ <br>
Das können wir nun als Aussage mit Termen $f(B_{\delta}^{d_x}(x))$ und $B_{\epsilon}^{d_y}(f(x))$, sowie Relation $R:=\subseteq$ darstellen.
Aus dem Term von $g(f(B_{\delta}^{d_x}(x)))$ wird unter Anwendung nun $g(B_{\epsilon}^{d_y}(f(x)))$. Und es gilt wegen der Transitivität gilt $g(f(B_{\delta}^{d_x}(x)))\subseteq g(B_{\epsilon}^{d_y}(f(x)))$, ein Schritt zum Beweis, dass die Konkatenation zweier stetiger Funktionen stetig ist.