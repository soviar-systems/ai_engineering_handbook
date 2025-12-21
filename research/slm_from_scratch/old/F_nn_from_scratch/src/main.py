import numpy as np

from neuron import Neuron


def main():
    """Run code."""
    X = np.array(
        [
            [-1, 2, 3, 13, 17],
            [4, -5, 6, 14, 18],
            [7, 8, -9, 15, 19],
            [-10, 11, 12, 16, -20],
        ],
        dtype=np.float64,
    )
    y = np.array([100, 200, 300, 400], dtype=np.float64)

    my_neuron = Neuron()
    dJ_dw, dJ_db = my_neuron.gradient(y_true=y, X=X)

    print("weights:", my_neuron.w)
    print("linear transformation:", my_neuron.z)
    print("activation:", my_neuron.a)
    print("dJ_dw:", dJ_dw)
    print("dJ_db:", dJ_db)  # print("my_neuron.input_size:", my_neuron.input_size)


if __name__ == "__main__":
    main()
