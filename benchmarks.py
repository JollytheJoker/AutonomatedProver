import time
from GraphBuilder import GraphBuilder
from MObject import Function, Quantor, Set
import numpy as np
import matplotlib.pyplot as plt
import timeit

# Benchmark CMR
def benchmark_cmr():
    times = []
    k_max = 2
    scale = np.array([i for i in range(1, k_max)])
    means = []
    stds = []
    for k in range(1, k_max):
        X = Set(association="X")

        f = Function(binding_quantity=(X, X), quantor=Quantor.DEFINE)
        g = Function(binding_quantity=(X, X), quantor=Quantor.DEFINE)

        # Graphs node repetitions (manually for now)
        n = 1000

        # Graph 1: A 6-cycle alternating between f and g, with edge weight 4 * n
        # from the root f into the cycle, plus an output edge to X.

        graph1 = GraphBuilder()

        # Nodes
        root_f = graph1.add_node(f, 1, X)

        gs = [graph1.add_node(g, 1, X) for _ in range(3 * k)]
        fs = [root_f] + [graph1.add_node(f, 1, X) for _ in range(3 * k - 1)]

        # Output node
        n_out = graph1.add_node(X, 0)

        graph1.set_root_node(root_f)

        for i in range(3 * k):
            if i == 0:
                e = graph1.add_edge(gs[i], (4 * n), fs[i])
            else:
                e = graph1.add_edge(gs[i], 1, fs[i])
            graph1.add_edge_to_slot(fs[i], e, 0)

            e = graph1.add_edge(fs[(i + 1) % (3 * k)], 1, gs[i])
            graph1.add_edge_to_slot(gs[i], e, 0)

        e_out = graph1.add_edge(n_out, 1, root_f)
        graph1.add_edge_to_slot(root_f, e_out, 0)

        root_node1 = graph1.build()

        # Graph 2: A root f with three independent 4-cycles, with initial
        # edge weights 3n - 1, 3n, and 1 respectively, plus an input edge to X.

        graph2 = GraphBuilder()

        root_f = graph2.add_node(f, 1, X)
        n_in = graph2.add_node(X, 0)

        graph2.set_root_node(root_f)

        for w in [3 * n - 1, 3 * n, 1]:
            gs = [graph2.add_node(g, 1, X) for _ in range(2 * k)]
            fs = [root_f] + [graph2.add_node(f, 1, X) for _ in range(2 * k - 1)]

            for i in range(2 * k):
                if i == 0:
                    e = graph2.add_edge(gs[i], w, fs[i])
                else:
                    e = graph2.add_edge(gs[i], 1, fs[i])
                graph2.add_edge_to_slot(fs[i], e, 0)

                e = graph2.add_edge(fs[(i + 1) % (2 * k)], 1, gs[i])
                graph2.add_edge_to_slot(gs[i], e, 0)

        e_in = graph2.add_edge(n_in, 1, root_f)
        graph2.add_edge_to_slot(root_f, e_in, 0)

        root_node2 = graph2.build()

        # Run evaluation test
        '''samples = 1000
        for _ in range(samples):
            if _ % 10 == 0:
                start = time.perf_counter()
            val = root_node1 == root_node2
            if (_ - 1) % 10 == 0:
                times.append((time.perf_counter() - start) / 10)
        times_np = np.array(times)
        means.append(np.average(times_np))
        stds.append(np.std(times_np))
        print(means[-1], stds[-1])'''

        raw_times = timeit.repeat(
            stmt=lambda: root_node1 == root_node2,
            repeat=100000,
            number=1
        )

        times_ms = np.array(raw_times) * 1000

        mean_val = np.mean(times_ms)
        std_val = np.std(times_ms)

        means.append(mean_val)
        stds.append(std_val)
        print(mean_val, std_val)

    # Plot
    plt.plot(scale, np.array(means) + np.array(stds), color='gray', linestyle='--', linewidth=1.2, alpha=0.5, label=r'$\pm 1\sigma$-Korridor')
    plt.plot(scale, np.array(means) - np.array(stds), color='gray', linestyle='--', linewidth=1.2, alpha=0.5)
    plt.plot(scale, np.array(means), color='yellow', linewidth=3, label=r'Mittelwert ($\mu$)')
    # Trendline
    z = np.polyfit(scale, means, 1)
    p = np.poly1d(z)

    plt.plot(
        scale, p(scale),
        color='red',
        linestyle='-.',
        linewidth=1,
        label=f'Trendlinie (m = {z[0]:.2e})'
    )

    plt.title('Laufzeitanalyse nach Skalierung der 6/4-Zyklen um Faktor $k$', fontsize=12, pad=12)
    plt.xlabel('Skalierungsfaktor $k$', fontsize=10)
    plt.ylabel('Laufzeit in ms', fontsize=10)
    plt.grid()
    plt.legend(frameon=True, facecolor='white', framealpha=1, loc='upper left')
    plt.tight_layout()
    plt.savefig('cmr_scaling.png', dpi=300)
    plt.show()

benchmark_cmr()
