import numpy as np

class Neuron:
    """Implement single neuron class."""

    def __init__(self, input_size):
        """Initialize neuron entity."""
        self.input_size = input_size
        self.w = np.random.default_rng().random(self.input_size)
        self.b = np.random.default_rng().random()
        # activation function hyperparameter
        self.alpha = 0.01

    def leaky_relu(self, vector):
        """Break linearity."""
        return np.maximum(self.alpha * vector, vector)

    def derivative_of_leaky_relu(self, vector):
        """Calculate the derivative of the activation function."""
        derivative = np.asarray(vector, copy=True)
        return np.where(derivative < 0, self.alpha, 1)

    def _get_linear_transformation(self, x):
        """Make the matrix multiplication of x and weights."""
        return np.dot(x, self.w) + self.b

    def forward(self, x):
        """Calculate forward pass with activation function."""
        z = self._get_linear_transformation(x)
        a = self.leaky_relu(z)
        return a

    def gradient_of_J(self, y_true, x):
        """Compute the gradient after forward pass."""
        y_pred = self.forward(x)
        error = y_pred - y_true

        leaky_relu_derivative = self.derivative_of_leaky_relu(self._get_linear_transformation(x))

        return np.dot((error * leaky_relu_derivative), x)
