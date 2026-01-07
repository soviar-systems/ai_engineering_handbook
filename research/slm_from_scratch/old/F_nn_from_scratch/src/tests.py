import numpy as np

from neuron import TestNeuron

# import pytest


def main():
    """Run main code."""
    test_cases = create_test_cases()
    print(len(test_cases))
    for i, case in enumerate(test_cases):
        print(i, case)


# def test_weight_updates(test_cases):
#    """Test all weight update scenarios from oracle."""
#    for case in test_cases:
#        neuron = Neuron()


def create_test_cases():
    """Create test cases for single neuron."""
    my_test = TestNeuron()

    # base test case - negative_gradients_increase_weights
    my_test.create_neuron_test_case()

    # Edge case: Zero gradients (no learning should occur)
    my_test.create_neuron_test_case(
        name="zero_gradients_no_change",
        y_true=np.array([1.2]),  # Exactly matches our forward pass output
    )

    # Edge case: Large learning rate
    my_test.create_neuron_test_case(
        name="large_learning_rate",
        y_true=np.array([2.0]),  # Larger error
        lr=0.1,  # 10x larger learning rate
    )

    # Batch input case (multiple examples)
    my_test.create_neuron_test_case(
        name="batch_input_gradients",
        X=np.array([[1.0, 2.0], [0.5, 1.0]]),  # 2 examples
        y_true=np.array([1.5, 0.8]),  # Batch targets
    )

    # Single feature case
    my_test.create_neuron_test_case(
        name="single_feature",
        X=np.array([[1.0]]),  # Single input feature
        y_true=np.array([0.5]),
        w=np.array([0.3]),
    )

    # Extreme values case
    my_test.create_neuron_test_case(
        name="extreme_gradients",
        X=np.array([[100.0, 200.0]]),  # Large inputs
        y_true=np.array([500.0]),  # Large target
        lr=0.001,  # Smaller LR for stability
    )

    return my_test.test_cases


if __name__ == "__main__":
    main()
