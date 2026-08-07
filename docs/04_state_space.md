# 04. Zustandsraum der Aussagen

## 1. Motivation
Wir wollen die Aussagen und deren Anwendung weiter verknüpfen können, um komplexe Beweise autonom zu finden. Ein Beweis einer Aussage ist formal die Transformation von einem Start/End-Expression tree zu dem jeweiliegen anderen Ende. Diese ExpressionTrees und Transformationen dieser zu neuen lassen sich als Zustände in einem Zustandsraum bzw. Graphen interpretieren.

## 2. Formalisierung
> **Beweise** <br>
> Der Beweis von einer Aussage $A=(T_S,R,T_E)$ ist eine fortwährende Anwendung der gegebenen Aussagen $\{A_i\}$. D.h., falls $\{i_n\}_{n\in\mathbb{N},n<N \in \mathbb{N}}$ existiert, sodass für $T_0=T_S, T_{n+1}=A_{i_n}(T_n) \implies T_N=T_E$ (bzw. analog mit $T_0=T_E,T_N=T_S$ und $ \{A^{-1}_i\}$), dann ist die Aussage bewiesen.

> **Definition (Zustandsgraphen)** <br>
> Sei $\Omega$ die Menge alle möglichen ExpressionTrees aus mathematischen Objekten. Für eine Aussagen Menge $\{A_i\}$ und Ziel-Aussage $A_G=(T_S,R,T_E)$ definiere $V(T_S,\{A_i\})\subseteq \Omega$ als die kleinste Menge, für die
> * $T_S \in V(T_S,\{A_i\})$
> * $T \in V(T_S,\{A_i\}) \implies A_i(T) \in V(T_S,\{A_i\}) \lor \lnot A_i(T)$ <br>
> Definiere ferner $E(T_S, \{A_i\})=\{(T, A(T) |T\in V(T_S, \{A_i\}), A\in\{A_i\})\}$ als Kantenmenge des Zustandsgraphen. Zuletzt definiere $G(T_S,\{A_i\})=(V(T_S,\{A_i\}), E(T_S,\{A_i\}))$ als gerichteten Graphen. Liegt $T_E \in V(T_S, \{A_i\})$, so gilt $A_G$, denn es existiert ein Pfad von $T_S$ zu $T_E$.<br>

Um den Umgekehrten Pfad zu finden und so auch die Aussage zu zeigen, muss $T_S \in V(T_E,\{A_i^{-1}\})$ gelten.

## 3. Implementierung
Wir definierenen einen neue Graphen-Klasse, die den Graphen nicht vorgenneriert, sondern rekursiv erstellt, wir wenden einfach die alle gegebenen Aussagen auf jeden momentanenen untersuchten front-Zustand an und speichern die nächsten. Falls wir von $T_S$ starten und $T_E$ erreichen, hat das Programm einen Beweis gefunden, anders herrum funkrioniert das auf selbe Weise (diese lässt später auch bidirektionale Zustandsraum suchen zu). Eine Zustandsraumsuche erfolgt mit einem Algorithmus (wie BFS, A* oder Greedy).

## 4. Beispiel
Wir nehmen wieder das Konkatenations Besipiel bzgl. Stetigkeit. Es seien $(X, d_x), (Y,d_y), (Z,d_z)$ metrische Räume und ferner $f:X\rightarrow Y, g:Y\rightarrow Z$ stetige Funktionen. Wir definieren nun die Aussagen $A_f, A_g$ als dessen Stetigkeit wie in vorigen Beispielen. Ferner ist unsere Ziel-Aussage $A_{fg}:=(T_S, \subseteq, T_E)$ mit $T_S, T_E$ auf bekannte Weise definiert. Die Anwendung der Stetigkeit von $g$ auf $T_E$ gibt uns $g(B_{\delta}^{d_y}(f(x))) \in A_g^{-1}(T_E)$. Ferner können wir nun die Stetigkeit von $f$ auf den Teilbaum $B_{\delta}^{d_y}(f(x))$ anwenden um insgesamt mit der Monotonie von $g$: $g(f(B_{\delta}^{d_x}(x)))=T_S \in A_f^{-1}(A_g^{-1}(T_E))$, was die Zielaussage - also Stetigkeit von $g(f)$ beweist.

