import numpy as np


class Neuron:
    """Implement single neuron class."""

    def __init__(self: "Neuron") -> None:
        """Initialize neuron entity."""
        self.w: np.ndarray = None
        self.b: np.float32 = np.float32(0.0)
        # linear transformation
        self.z: np.ndarray = None
        # activation transformation
        self.a: np.ndarray = None
        # activation function hyperparameter
        self.alpha: np.float32 = np.float32(0.01)
        # learning rate for weights update
        self.lr: np.float32 = np.float32(0.01)

    def activation(
        self,
        alpha: np.float32 = None,
        activation_algorithm: str = "leaky_relu",
    ):
        """Break linearity."""
        if alpha is not None:
            self.alpha = alpha
        if activation_algorithm == "leaky_relu":
            self.a = np.maximum(self.alpha * self.z, self.z)
        else:
            raise ValueError(
                f"Activation function {activation_algorithm} not implemented (yet)"
            )

    def forward(
        self,
        X: np.ndarray,
        alpha: np.float32 = None,
        activation_algorithm: str = "leaky_relu",
    ) -> np.ndarray:
        """Calculate forward pass with activation function."""
        # Xavier/Glorot weights initialization
        if self.w is None:
            # size of one example
            self.input_size = X.shape[-1]
            self.w = (np.random.default_rng().random(self.input_size) - 0.5) * np.sqrt(
                2.0 / self.input_size
            )

        # compute linear transformation
        self.z = np.dot(X, self.w) + self.b

        # compute activation transformation
        self.activation(alpha, activation_algorithm)

        return self.a

    def gradient_of_a(self, activation_algorithm: str = "leaky_relu"):
        """Compute a'."""
        if activation_algorithm == "leaky_relu":
            da_dz = np.where(self.z < 0, self.alpha, 1)
        else:
            raise ValueError(
                f"Activation function {activation_algorithm} not implemented (yet)"
            )

        return da_dz

    def gradient(
        self,
        X: np.ndarray,
        y_true: np.ndarray,
        alpha: np.float32 = None,
        activation_algorithm: str = "leaky_relu",
    ) -> np.ndarray:
        """Gradients for squared error loss: J = (y_pred - y_true)^2 / 2."""
        # X and y_pred shape check
        batch_size = X.shape[0]
        y_true_number = y_true.shape[0]
        if batch_size != y_true.shape[0]:
            raise ValueError(
                f"Batch size of X={batch_size} must be of y_pred={y_true_number} size."
            )

        # make forward pass
        self.forward(
            X,
            alpha=alpha,
            activation_algorithm=activation_algorithm,
        )

        # compute J', where J is MSE
        dJ_da = (self.a - y_true) / batch_size

        # compute a'
        da_dz = self.gradient_of_a(activation_algorithm=activation_algorithm)

        # compute complete gradients
        dJ_dw = np.dot((dJ_da * da_dz), X)
        dJ_db = np.sum(dJ_da * da_dz)

        return dJ_dw, dJ_db


class TestNeuron:
    """Test Neuron class."""

    def __init__(self: "TestNeuron") -> None:
        """Initialize test class."""
        self.test_cases: list = list()

    def create_neuron_test_case(
        self,
        name: str = "negative_gradients_increase_weights",
        X: np.ndarray = np.array([[1.0, 2.0]]),
        y_true: np.ndarray = np.array([1.5]),
        w: np.ndarray = np.array([0.3, 0.4]),
        b: np.float32 = np.float32(0.1),
        lr: np.float32 = np.float32(0.01),
        activation: str = "leaky_relu",
        cost_f: str = "mse",
    ):
        """
        Create a complete single neuron test case.

        Base case is negative gradient which inscreases weights.
        """
        # final result
        result = {
            "name": name,
            "initial_X": X,
            "y_true": y_true,
            "initial_w": w,
            "initial_b": b,
            "learning_rate": lr,
        }

        # linear transformation
        z = np.dot(X, w) + b
        result["z"] = z

        # activation function
        alpha = 0.01
        if activation == "leaky_relu":
            a = np.maximum(z * alpha, z)
        result["a"] = a

        # backpropagation

        # cost function and its derivative
        batch_size = X.shape[0]
        if cost_f == "mse":
            # error
            u = a - y_true
            # cost function
            J = (1 / 2) * (1 / batch_size) * u**2
            # J'
            dJ_da = (1 / batch_size) * u
        else:
            raise ValueError(f'Cost function "{cost_f}" is not implemented yet.')

        result["J"] = J
        result["dJ_da"] = dJ_da

        # a'
        da_dz = np.where(z < 0, alpha, 1)
        result["da_dz"] = da_dz

        # z'
        dz_dw = X
        result["dz_dw"] = dz_dw

        # b'
        dz_b = 1
        result["dz_b"] = dz_b

        dJ_dw = np.dot(dJ_da * da_dz, dz_dw)  # where dz_dw = X
        result["dJ_dw"] = dJ_dw

        dJ_db = np.sum(dJ_da * da_dz) * dz_b  # where dz_b = 1
        result["dJ_db"] = dJ_db

        # w - lr * (-gradient) = w + lr*|gradient|
        result["expected_w"] = np.subtract(w, (lr * dJ_dw))
        result["expected_b"] = np.subtract(b, (lr * dJ_db))

        self.test_cases.append(result)

        return self.test_cases
