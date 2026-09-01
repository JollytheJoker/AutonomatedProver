# 01. Grammatik und Syntax

## 1. Motivation
Um logische Aussagen über alle Themengebiete formel richtig abzubilden, müssen wir Bausteiene katorisieren.
Wir unterteilen hierbei in Funktionen und Mengen. Variablen werden als Elemente von Mengen kategorisiert, zählen formell aber als Menge

## 2. Formale Definition
> **Definition (Mathematisches Objekt)** <br>
> Ein mathematisches Objekt ist ein Tuple $(\mathcal{T}, \mathcal{B}, \Delta, \mathcal{Q}, \mathrm{id})$, wobei
> 1. **Typ $(\mathcal{T})$:** Entweder *Menge* $(\mathscr{M})$ oder *Funktion* $(\mathscr{F})$. Diese bestimmen die Weitere Form des Tupels.
> 2. **Bindungsbedingung $(\mathcal{B}): $** Bestimmt die Domäne, in der das Objekt fungiert.
>   * Für eine Menge kann das Tupel eine beliebige Größe haben (insb. kann es auch leer sein)
>   * Das $\mathcal{B}$-Tupel für eine Funktion hat genau zwei Einträge: Eine Urbild- und Bildmenge, diese müssen vom Typ Menge sein. 
> 3. **Verschachtelungstiefe $(\Delta)$:** Für Objekte vom Typ Funktion, ist $\Delta=1$. Für Mengen, kann man über die Verschachtelungstiefe Potenzmengen bilden, es gilt heuristisch:
>   $\text{self} \subseteq \mathcal{P}^{\Delta - 1}(\mathcal{B})$, für $\Delta \ge 1$, sonst $\text{self} \in \mathcal{B}$
> 4. **Quator $(\mathcal{Q})$:** Geben die Anzahl von Objekten an. Wir nutzen 
>   * $\forall$: Für alle Objekte die diese Bindungsgedingung erfüllen
>   * $\exists$: Es existiert mind. ein Objekte, welches eine Bindungsbedingung erfüllt
>   * $D$: Definiere ein Objekt, welches seine Bindungsbedingung erfüllt (alle Urmengenen müssen definiert werden)
> 5. **Identifikator $(\mathrm{id}): $** Eine Zahl, welche zur Unterscheidung verschiedener mathematischer Objekter gleicher Werte in $\mathcal{T}, \mathcal{B}, \mathcal{M}, \mathcal{Q}$ dient.

## 3. Übersicht der mathematischen Objekte
In der Implementierung definieren mathematische objekte als statische Objekte mit eigenschaften $(\mathcal{B}, \Delta, \mathcal{Q}, \mathrm{id})$; für lesbarkeit fürgen wir das Attribut eines Assoziations-String hinzu. Der Typ wird als Vererbung auf zwei unter Klassen verteilt.

## 4. Beispiel
Wir wollen eine Funktion $f:A\rightarrow Y$ definieren, wobei $A \subseteq X$ ist. Dies erfordert eine Schrittweise Definition von Objekten nach der Tupel-Struktur:
* 1. **Urbildmenge $X$:** Wir definieren eine ungebundene Menge $X$. $X=(\mathscr{M}, (), 1, D, 0)$
* 2. **Bildmenge $Y$:** Eine zweite ungebundene Menge, mit anderen $\mathrm{id}$ sei $Y=(\mathscr{M}, (), 1, D, 1)$
* 3. **Teilmenge $A$:** Die Teilmenge A sei an X gebunden ($A \subseteq X$). $A=(\mathscr{M}, (X), 1, D, 0)$
* 4. **Element $x \in A$:** Das Element $x\in A$ ist definiert als $x=(\mathscr{M}, (A), 0, D, 0)$, also $\Delta=0$.
* 5. **Funktion $f$:** Die Funktion von A nach Y ist dann $f=(\mathscr{F}, (A, Y), 1, D, 0)$

Wenn wir $f$ nicht mit assoziationen schreiben wollen, wäre das: $$f = (\mathscr{F}, ((\mathscr{M}, ((\mathscr{M}, \emptyset, 1, D, 0)), 1, D, 2), (\mathscr{M}, \emptyset, 1, D, 1)), 1, D, 3)$$
