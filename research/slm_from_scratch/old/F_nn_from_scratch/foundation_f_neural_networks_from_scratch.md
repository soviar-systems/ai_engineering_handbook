# FOUNDATION F: NEURAL NETWORKS FROM SCRATCH

# <b>F.1 Gradient</b>

**The Core Idea**: A neural network is just a mathematical function that can be represented as a computational graph. The "learning" happens by adjusting the parameters of this function to minimize some error.

Think about a single neuron - the simplest building block. If you were to implement this from scratch in NumPy (no PyTorch yet), what would be the minimal components you'd need?

Consider:
- What inputs does it take?
- What parameters does it have? 
- What computation does it perform?
- What output does it produce?

1. **Linear combination**: $y = w_1x_1 + w_2x_2 + \ldots + w_nx_n + b$
2. **Weights initialization**: Random values
3. **Activation function**: Breaks linearity
4. **Matrix operations**

## The Linear Algebra Gap

Think about processing one input vector vs many inputs:

**Single input**: $[x_1, x_2, x_3]$ with weights $[\theta_1, \theta_2, \theta_3]$  
$output = x_1\theta_1 + x_2\theta_2 + x_3\theta_3 + b$

**Multiple inputs (as matrix)**: 
```
Inputs: [ [x₁₁, x₁₂, x₁₃],   Weights: [𝜃₁, 𝜃₂, 𝜃₃]ᵀ
          [x₂₁, x₂₂, x₂₃],
          [x₃₁, x₃₂, x₃₃] ]
```

What linear algebra operation would efficiently compute all outputs at once? Matrix multiplication.

## Single neuron code

Try implementing the **single input case** first:

```python
import numpy as np

class Neuron:
    def __init__(self, input_size):
        # Initialize weights and bias here
        pass
    
    def forward(self, x):
        # Compute y = w·x + b
        # Then apply activation function
        pass
```

## Activation Function Options

| Function | Formula | Range | Key Properties |
|----------|---------|-------|----------------|
| **Sigmoid** | 1/(1+e⁻ˣ) | (0,1) | Smooth, bounded, but can saturate (vanishing gradients) |
| **Tanh** | (eˣ-e⁻ˣ)/(eˣ+e⁻ˣ) | (-1,1) | Zero-centered, but still can saturate |
| **ReLU** | max(0,x) | [0,∞) | Simple, avoids saturation, but "dying ReLU" problem |
| **Leaky ReLU** | max(0.01x,x) | (-∞,∞) | Fixes dying ReLU, small gradient for negatives |

**Historical Context & Modern Practice**

- **1980s-2000s**: Sigmoid/tanh were dominant (biological plausibility)
- **2010s**: ReLU became standard for hidden layers (training speed)
- **Today**: Variants like Leaky ReLU, GELU are common

For your **first from-scratch implementation**, which activation function would you choose and **why**? Consider:

1. **Simplicity of implementation**
2. **Gradient behavior** (important for backpropagation)
3. **Training stability**



Leaky ReLU is actually a very smart pick for your first implementation.

**Why Leaky ReLU is a Great Choice**

1. **Simple to implement** - just `max(0.01*x, x)` 
2. **Avoids the "dying neuron" problem** of regular ReLU
3. **Computationally efficient** - no expensive exponentials like sigmoid/tanh
4. **Good gradient flow** - never completely zero gradient

**Your Implementation Challenge**

Now, here's what I want you to think about for the implementation:

```python
def leaky_relu(x, alpha=0.01):
    # Your implementation here
    pass
```

**Key consideration**: Should this be a method of your `Neuron` class, or a separate function? What are the trade-offs?

Also think about: How will this affect your backpropagation implementation later? (We'll get to that soon)

Putting the activation function in the forward pass is exactly right.

**Your Architectural Decision Makes Sense**

Having the activation as part of the neuron's forward pass:
- Keeps the neuron self-contained
- Makes the computation clear: `output = activation(linear_combination)`
- Will make backpropagation more straightforward (when we get there)

### Code implementation


```python
import numpy as np


class Neuron:
    """Implement single neuron class."""

    def __init__(self, input_size: tuple) -> None:
        """Initialize neuron entity."""
        self.input_size = input_size
        self.w = np.random.default_rng().random(self.input_size[-1])
        self.b = np.random.default_rng().random()
        # activation function hyperparameter
        self.alpha = 0.01

    def leaky_relu(self, vector: np.array) -> np.array:
        """
        Break linearity.

        Parameters
        ----------
        vector : np.array
            y_pred before activation function applied.

        """
        return np.maximum(self.alpha * vector, vector)

    def _get_linear_transformation(self, x: np.array) -> np.array:
        """
        Make the matrix multiplication of x and weights.

        The result is y_pred before activation function.
        """
        return np.dot(x, self.w) + self.b

    def forward(self, x: np.array) -> np.array:
        """Calculate forward pass with activation function."""
        vector = self._get_linear_transformation(x)
        return self.leaky_relu(vector)
```


```python
X = np.array(
    [
        [-1, 2, 3, 13, 17],
        [4, -5, 6, 14, 18],
        [7, 8, -9, 15, 19],
        [-10, 11, 12, 16, -20],
    ],
    dtype=np.float64,
)

my_neuron = Neuron((X.shape))
print("my_neuron.input_size:", my_neuron.input_size)
print("my_neuron.w:", my_neuron.w)
print("linear transformation:", my_neuron._get_linear_transformation(X))
print("my_neuron.forward(X):", my_neuron.forward(X))
```

    my_neuron.input_size: (4, 5)
    my_neuron.w: [0.96963449 0.88127309 0.29762979 0.32335681 0.75624471]
    linear transformation: [19.55678708 20.20853882 31.18914713 -5.57078139]
    my_neuron.forward(X): [19.55678708 20.20853882 31.18914713 -0.05570781]


## Gradient derivation

Your single neuron implementation is solid. The next critical concept is: **how does learning actually happen?**

We have this neuron that can compute outputs, but how do we adjust `self.w` and `self.b` to make it produce better outputs?

What's your current understanding of how the "learning" process works in neural networks?

You've identified the three key components:

1. **Error/Loss**
2. **Gradient**
3. **Weight Update**

### The Missing Piece: Backpropagation

What you described is **gradient descent**. The magic that makes it work for neural networks is **backpropagation** - the algorithm for efficiently computing those gradients through the entire computational graph.

Think of it this way: If your neuron's computation is:
```
input → linear → activation → output
```

Backpropagation answers:

> "*How much did each weight contribute to the final error?*"

Let's break this down into manageable steps. If you were to implement gradient calculation for your single neuron, what would be the minimal information you'd need?

Consider:
- The error at the output
- How the activation function affects the gradient
- How the linear combination affects the gradient

### The Error Signal Flow

The error signal begins with the difference between predicted and true values.

You're correct: `error = true_y - predicted_y` (or some function of this difference)

Now here's the key insight for backpropagation: **We need to trace how this error flows backward through each operation.**

Think about your neuron's forward pass:
```
x → linear (w·x + b) → leaky_relu → y_pred
```

For backpropagation, we go backward:
```
error ← d_leaky_relu ← d_linear ← gradients for w and b
```

If you were to implement this gradient calculation manually for a single input, what operations would you need to compute?

Consider:
1. Gradient of the error with respect to the output
2. How the activation function transforms this gradient
3. How the linear operation distributes gradients to weights and bias

**What's your thinking about the mathematical operations involved?**

### Chain Rule Intuition

Think about your neuron's computation:
```
output = leaky_relu(w·x + b)
error = (true_y - output)²
```

If we want to know how much to change `w₁`, we need to answer: "How does changing `w₁` affect the final error?"

This is where the **chain rule** from calculus comes in. We break the problem into steps:

1. How does error change with output?
2. How does output change with activation input?
3. How does activation input change with `w₁`?

You've done exactly the right preparation. Re-reading the math and connecting it to CS229 shows excellent learning discipline.

Your understanding is spot on:

- **J(θ)** is our cost function (like MSE)
- **Partial derivatives** give us the gradient ∇J(θ)  
- **Gradient descent** uses this to update weights: θ = θ - α∇J(θ)

You asked: *"Do we really need to work with the error itself?"* The answer reveals the elegance of backpropagation:

> We don't actually need the explicit mathematical formula for J(θ). 

Instead, we use the **chain rule** to compute gradients through the computational graph.

Think about your neuron:
```
x → z = w·x + b → a = leaky_relu(z) → J = (y_true - a)²
```

To find $\displaystyle \frac {\partial}{\partial \theta}J(\theta)$, we can compute:

$$
\frac {\partial}{\partial \theta}J(\theta) = \frac {\partial J(\theta)}{\partial a} \times \frac {\partial a}{\partial z} \times \frac {\partial z}{\partial \theta}
$$

**Your implementation challenge**: If you were to compute these partial derivatives numerically for a single example, what would be your step-by-step approach?

(see CS229, Batch Gradient Descent)
\begin{align*}
\frac {\partial}{\partial \theta_j} J(\theta) & = \frac {\partial}{\partial \theta_j} \frac{1}{2} \left(h_{\theta}(x) - y\right)^2 = \\
& = 2 \frac {1}{2} (h_{\theta}(x) - y) \cdot \frac {\partial}{\partial \theta_j}(h_{\theta}(x) - y) = \\
& = (h_{\theta}(x) - y) \cdot \frac {\partial}{\partial \theta_j} (\theta_0 x_0 + \theta_1 x_1 + \cdots + \theta_j x_j \cdots + \theta_n x_n -y) \\
& = (h_{\theta}(x) - y) \cdot x_j
\end{align*}

You've derived the gradient for linear regression perfectly! 

Your derivation:

$$
\frac {\partial}{\partial \theta_j} J(\theta) = (h_{\theta}(x) - y) \cdot x_j
$$

The gradient for each weight is proportional to:
1. The **error signal** (prediction - true value)
2. The **input** that weight connects to

Your neuron has one extra step: the activation function. So the chain becomes:

For weight $\theta_j$:

$$
\frac {\partial}{\partial \theta_j}J(\theta) = \frac {\partial J(\theta)}{\partial a} \times \frac {\partial a}{\partial z} \times \frac {\partial z}{\partial \theta_j}
$$

Where:
- $a = \text {leaky_relu}(z)$ = final output
- $z = \theta x + b$ = linear combination
- $\displaystyle \frac {\partial z}{\partial \theta_j} = x_j$ (as you correctly derived)

Given your `leaky_relu` function:
```python
def leaky_relu(self, vector, alpha=0.01):
    return np.maximum(alpha * vector, vector)
```

What would be the derivative $\displaystyle \frac {\partial a}{\partial z}$? Think about how `leaky_relu` behaves differently for positive vs negative inputs.

For `leaky_relu`:

- if `z > 0`: $a = z$, so $\displaystyle \frac {\partial a}{\partial z} = 1$
- if `z <= 0`: $a = \alpha \cdot z$, so $\displaystyle \frac {\partial a}{\partial z} = \alpha$


### Code implementaion

Now you have all the pieces for the gradient:

$$
\frac {\partial J}{\partial \theta_j} = (a - y_{true}) \cdot [\text {derivative_of_leaky_relu}(z)] \cdot x_j
$$

Where $[\text {derivative_of_leaky_relu}(z)]$ is $[1\ \text {or}\ \alpha]$ depends on whether $z$ was positive or negative.

**Before you implement**: How would you handle computing this derivative efficiently in code, given that `z` might be a single value or a batch of values?

How would you compute the gradient for all weights simultaneously, such that each weight $\theta_j$ gets:

$$
\text {gradient}[\theta_j] = \text {sum_over_examples} (\ \text {error} \cdot \text {derivative} \cdot x_j\ )
$$

What's your thinking about the vectorized operation needed here?


```python
import numpy as np


class Neuron:
    """Implement single neuron class."""

    def __init__(self, input_size: tuple) -> None:
        """Initialize neuron entity."""
        self.input_size = input_size
        self.w = np.random.default_rng().random(self.input_size[-1])
        self.b = np.random.default_rng().random()
        # activation function hyperparameter
        self.alpha = 0.01

    def leaky_relu(self, vector: np.array) -> np.array:
        """
        Break linearity.

        Parameters
        ----------
        vector : np.array
            y_pred before activation function applied.

        """
        return np.maximum(self.alpha * vector, vector)

    def derivative_of_leaky_relu(self, vector: np.array) -> np.array:
        """
        Calculate the derivative of the activation function.

        Parameters
        ----------
        vector : np.array
            y_pred before activation function applied.

        """
        derivative = np.asarray(vector, copy=True)
        return np.where(derivative < 0, self.alpha, 1)

    def _get_linear_transformation(self, x: np.array) -> np.array:
        """
        Make the matrix multiplication of x and weights.

        The result is y_pred before activation function.
        """
        return np.dot(x, self.w) + self.b

    def forward(self, x: np.array) -> np.array:
        """Calculate forward pass with activation function."""
        vector = self._get_linear_transformation(x)
        return self.leaky_relu(vector)

    def gradient_of_J(self, y_true: np.array, x: np.array) -> np.array:
        """Compute the gradient after forward pass."""
        y_pred = self.forward(x)
        error = y_pred - y_true

        leaky_relu_derivative = self.derivative_of_leaky_relu(
            self._get_linear_transformation(x)
        )

        return np.dot((error * leaky_relu_derivative), x)
```


```python
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

my_neuron = Neuron((X.shape))
print("my_neuron.input_size:", my_neuron.input_size)
print("my_neuron.w:", my_neuron.w)
print("linear transformation:", my_neuron._get_linear_transformation(X))
print("my_neuron.forward(X):", my_neuron.forward(X))
print(
    "my_neuron.gradient_of_J(y_true=y, x=X):",
    my_neuron.gradient_of_J(y_true=y, x=X),
)
```

    my_neuron.input_size: (4, 5)
    my_neuron.w: [0.92542368 0.63684431 0.63029109 0.48955112 0.96805626]
    linear transformation: [25.99848804 29.51617692 32.5746651  -5.27553477]
    my_neuron.forward(X): [25.99848804 29.51617692 32.5746651  -0.05275535]
    my_neuron.gradient_of_J(y_true=y, x=X): [-2439.9058491  -1478.99239077  1113.91420904 -7424.18164295
     -9327.80533079]


I've carefully reviewed your code and this is a **massive improvement**. You've solved the key issues beautifully.

**What You Fixed Perfectly ✅**

1. **Correct derivative application**: Using `_get_linear_transformation(x)` as input to the derivative
2. **Proper vectorization**: `error * leaky_relu_derivative` element-wise multiplication
3. **Efficient gradient computation**: `np.dot((error * leaky_relu_derivative), x)` is exactly right!

**Your Solution is Mathematically Correct**

Let's trace the dimensions:
- `error`: shape `(4,)` 
- `leaky_relu_derivative`: shape `(4,)`
- `error * leaky_relu_derivative`: shape `(4,)` (element-wise)
- `x`: shape `(4, 5)`
- `np.dot(..., x)`: shape `(5,)` - perfect! One gradient per weight

## Progress Summary

You've successfully:
- ✅ Implemented a single neuron with Leaky ReLU activation
- ✅ Derived and implemented backpropagation gradients
- ✅ Created a working gradient computation for batch inputs

**Major Conceptual Milestone Achieved**

You've now bridged the gap from theoretical understanding to practical implementation of neural network fundamentals. Your gradient computation is mathematically sound and efficiently vectorized.

## Ready for the Next Step?

Your gradient computation is working! The natural progression is:
1. **Weight update**: Use these gradients to actually train the neuron
2. **Training loop**: Implement gradient descent
3. **Test on real data**: See if it can learn a simple function

**What would you like to tackle next - the weight update or creating a training loop?**

# <b>F.2</b>


















