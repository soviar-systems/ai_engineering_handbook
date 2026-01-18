---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# FOUNDATION F: NEURAL NETWORKS FROM SCRATCH

+++

**The Core Idea**: A neural network is just a mathematical function that can be represented as a computational graph. The "learning" happens by adjusting the parameters of this function to minimize some error.

+++

# <b>1. Forward Pass</b>

+++

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

+++

# 1.1 The Linear Algebra Gap

+++

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

+++

# 1.2 Single neuron code

+++

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

+++

# 1.3 Activation Function Options

+++

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

+++

Putting the activation function in the forward pass is exactly right.

**Your Architectural Decision Makes Sense**

Having the activation as part of the neuron's forward pass:
- Keeps the neuron self-contained
- Makes the computation clear: `output = activation(linear_combination)`
- Will make backpropagation more straightforward (when we get there)

+++

# 1.4 Code implementation

```{code-cell} ipython3
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

```{code-cell} ipython3
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

## Weight Initialization Bug

+++

Your reasoning is correct about avoiding zeros, but the implementation has scaling issues:

```python
# Current: weights in [0.001, 1.001)
self.w = np.random.default_rng().random(input_size) + 0.001

# Problem: Large weights cause large pre-activations → gradient explosion
# Better: Xavier/Glorot initialization for linear layers
self.w = (np.random.default_rng().random(input_size) - 0.5) * np.sqrt(2.0 / input_size)
```

The `+ 0.001` only solves the "dead neuron" problem for ReLU, but creates gradient instability.

+++

## Type Hint Best Practices

+++

For deep learning systems:

```python
# Standard practice:
import numpy.typing as npt

class Neuron:
    def forward(
        self,
        X: npt.NDArray[np.float32],  # Consistent precision
        activation_f: str = "leaky_relu",
    ) -> npt.NDArray[np.float32]:
        
    # Use float32 throughout for GPU compatibility
    self.w: npt.NDArray[np.float32] = None  
    self.b: np.float32 = np.float32(0.0)
    self.lr: np.float32 = np.float32(0.01)
```

**Rationale:** GPUs are optimized for float32, and mixed precision causes unnecessary casting.

+++

# <b>2. Gradient derivation</b>

+++

Your single neuron implementation is solid. The next critical concept is: **how does learning actually happen?**

We have this neuron that can compute outputs, but how do we adjust `self.w` and `self.b` to make it produce better outputs?

What's your current understanding of how the "learning" process works in neural networks?

You've identified the three key components:

1. **Error/Loss**
2. **Gradient**
3. **Weight Update**

+++

# 2.1 The Missing Piece: Backpropagation

+++

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

+++

## The Error Signal Flow

+++

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

+++

## Chain Rule Intuition

+++

Think about your neuron's computation:
```
output = leaky_relu(w·x + b)
error = some_cost_function()
```

If we want to know how much to change $\omega_1$, we need to answer: "How does changing $\omega_1$ affect the final error?"

This is where the **chain rule** (производная сложной функции) from calculus comes in. We break the problem into steps:

1. How does error change with output?
2. How does output change with activation input?
3. How does activation input change with $\omega_1$?

+++

You've done exactly the right preparation. Re-reading the math and connecting it to CS229 shows excellent learning discipline.

Your understanding is spot on:

- $J(\theta)$ is our cost function (like MSE)
- **Partial derivatives** give us the gradient $\nabla J(\theta)$
- **Gradient descent** uses this to update weights: $\theta = \theta - \alpha\nabla J(\theta)$

You asked: *"Do we really need to work with the error itself?"* The answer reveals the elegance of backpropagation:

> We don't actually need the explicit mathematical formula for $J(\theta)$.

Instead, we use the **chain rule** to compute gradients through the **computational graph**.

Think about your neuron:
```
x → z = 𝜃·x + b → a = leaky_relu(z) → J = cost_function(a, y_true)
```

where `a` is `y_pred`.

To find $\displaystyle \frac {\partial}{\partial \theta}J(\theta)$, we can compute:

$$
\frac {\partial}{\partial \theta}J(\theta) = \frac {\partial J(\theta)}{\partial a} \times \frac {\partial a}{\partial z} \times \frac {\partial z}{\partial \theta}
$$

**Your implementation challenge**: If you were to compute these partial derivatives numerically for a single example, what would be your step-by-step approach?

+++

## Cost function `J`

+++

Let's define the cost function we're going to use. Modern frameworks such as [PyTorch](https://www.digitalocean.com/community/tutorials/pytorch-loss-functions) and TensorFlow define **Mean Squared Error (MSE)** with mean reduction by default.

This keeps the loss and gradients **batch-size invariant**, so that hyperparameters (like learning rate) can be reused independently of the dataset or mini-batch size.

$$
J(\theta) = \frac{1}{m} \cdot \frac{1}{2} \sum_{i=1}^m (h_\theta(x^{(i)}) - y^{(i)})^2
$$
$$
\nabla_\theta J(\theta) = \frac{1}{m} \sum_{i=1}^m (h_\theta(x^{(i)}) - y^{(i)}) \cdot x^{(i)}
$$

**Why average matters:**
- Without `/m`, your gradients grow linearly with batch size
- Learning rate becomes batch-size dependent
- Large batches cause instability

+++

For one example it is going to be:

\begin{align*}
\frac {\partial}{\partial \theta_j} J(\theta) & = \frac {\partial}{\partial \theta_j} \frac{1}{2} \left(h_{\theta}(x) - y\right)^2 = \\
& = 2 \frac {1}{2} (h_{\theta}(x) - y) \cdot \frac {\partial}{\partial \theta_j}(h_{\theta}(x) - y) = \\
& = (h_{\theta}(x) - y) \cdot \frac {\partial}{\partial \theta_j} (\theta_0 x_0 + \theta_1 x_1 + \cdots + \theta_j x_j \cdots + \theta_n x_n -y) \\
& = (h_{\theta}(x) - y) \cdot x_j
\end{align*}

You've derived the gradient for linear regression perfectly! 

$$
\frac {\partial}{\partial \theta_j} J(\theta) = (h_{\theta}(x) - y) \cdot x_j
$$

The gradient for each weight is proportional to:
1. The **error signal** (prediction - true value)
2. The **input** that weight connects to.

+++

## Activation function `a`

+++

Your neuron has one extra step: the activation function. So the chain becomes:

For weight $\theta_j$:

$$
\frac {\partial}{\partial \theta_j}J(\theta) = \frac {\partial J(\theta)}{\partial a} \times \frac {\partial a}{\partial z} \times \frac {\partial z}{\partial \theta_j}
$$

Where:
- $a = \text {leaky relu}(z)$ = final output (`y_pred`)
- $z = \theta x + b$ = linear combination
- $\displaystyle \frac {\partial z}{\partial \theta_j} = x_j$ (as you correctly derived)

Given your `leaky_relu` function:
```python
def leaky_relu(self, self.z, alpha=0.01):
    return np.maximum(alpha * self.z, self.z)
```

What would be the derivative $\displaystyle \frac {\partial a}{\partial z}$? Think about how `leaky_relu` behaves differently for positive vs negative inputs.

For `leaky_relu`:

- if `z > 0`: $a = z$, so $\displaystyle \frac {\partial a}{\partial z} = 1$
- if `z <= 0`: $a = \alpha \cdot z$, so $\displaystyle \frac {\partial a}{\partial z} = \alpha$

+++

# 2.2 Code implementaion

+++

Now you have all the pieces for the gradient:

$$
\frac {\partial J}{\partial \theta_j} = (a - y_{true}) \cdot [\text {activation derivative}(z)] \cdot x_j
$$

Where $[\text {activation derivative}(z)]$ is $[1\ \text {or}\ \alpha]$ depends on whether $z$ was positive or negative.

**Before you implement**: How would you handle computing this derivative efficiently in code, given that `z` might be a single value or a batch of values?

How would you compute the gradient for all weights simultaneously, such that each weight $\theta_j$ gets:

$$
\text {gradient}[\theta_j] = \text {sum over examples} (\ \text {error} \cdot \text {derivative} \cdot x_j\ )
$$

What's your thinking about the vectorized operation needed here?

```{code-cell} ipython3
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

```{code-cell} ipython3
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

+++

## Missing Bias Gradient

+++

**Problem**: Your `gradient_of_J` returns only `dJ_d𝜃` but completely omits `dJ_db`!

**Mathematical Reason**: 
- For bias: $\displaystyle \frac{\partial z}{\partial b} = 1$ where $z = \theta \cdot x + b$ (and it is always true because we always have $b^1 => 1$)
- Therefore: $\displaystyle \frac{\partial J}{\partial b} = \frac{\partial J}{\partial a} \cdot \frac{\partial a}{\partial z} \cdot \frac{\partial z}{\partial b}= \text{error} \times \text{activation_derivative} \times 1$

+++

**Visualizing the Bias Gradient**

Think of our neuron processing a batch of 4 examples:

```
Example 1: x₁ → z₁ = 𝜃·x₁ + b → a₁ = leaky_relu(z₁) → J = (y_true - a₁)²
Example 2: x₂ → z₂ = 𝜃·x₂ + b → a₂ = leaky_relu(z₂) → J = (y_true - a₂)²
Example 3: x₃ → z₃ = 𝜃·x₃ + b → a₃ = leaky_relu(z₃) → J = (y_true - a₃)²
Example 4: x₄ → z₄ = 𝜃·x₄ + b → a₄ = leaky_relu(z₄) → J = (y_true - a₄)²
```

**Key Insight**: The same bias `b` affects **every example** in the batch!

**Mathematical Derivation**

For squared error loss: $$J = \frac{1}{2} \sum_{i=1}^{m} (y_{pred}^{(i)} - y_{true}^{(i)})^2$$

Let's trace the gradient flow for bias:

1. **For one example**: $\displaystyle \frac{\partial J^{(i)}}{\partial b} = (y_{pred}^{(i)} - y_{true}^{(i)}) \cdot \text{leaky_relu}'(z^{(i)}) \cdot 1$

2. **For the whole batch**: $\displaystyle \frac{\partial J}{\partial b} = \sum_{i=1}^{m} \frac{\partial J^{(i)}}{\partial b}$

So: `dJ_db = sum_over_all_examples(error * activation_derivative)`

**Why Sum Instead of Average?**

Let's see what happens with a concrete batch:

```python
# Example batch of 4 examples
errors = [0.5, -0.2, 0.3, -0.1]           # y_pred - y_true
derivatives = [1.0, 0.01, 1.0, 0.01]      # leaky_relu_derivative

# Correct: SUM (total effect of bias on all examples)
dJ_db = (0.5*1.0) + (-0.2*0.01) + (0.3*1.0) + (-0.1*0.01) = 0.5 - 0.002 + 0.3 - 0.001 = 0.797

# Wrong: AVERAGE (would underestimate total bias contribution)
dJ_db_avg = 0.797 / 4 = 0.199  # This would make bias updates 4x too small!
```

**The intuition**: Bias is a **shared parameter** across all examples, so we need to accumulate its effect from the entire batch.

**Now Let's Compare with Weight Gradients**

For weights, each weight connects to specific input features:

```
Example 1: w·x₁ = w₁·x₁₁ + w₂·x₁₂ + ... + wₙ·x₁ₙ  
Example 2: w·x₂ = w₁·x₂₁ + w₂·x₂₂ + ... + wₙ·x₂ₙ
```

The gradient for weight wⱼ comes from: $\displaystyle \frac{\partial J}{\partial w_j} = \sum_{i=1}^{m} (\text{error}^{(i)} \cdot \text{derivative}^{(i)} \cdot x_{ij})$

This is exactly what `np.dot(error * derivative, x)` computes!

**Let's Build This Understanding Together**

**Step 1**: Does the "bias affects all examples equally" intuition make sense?

**Step 2**: Can you see why we sum across examples for bias gradient but use dot product for weights?

+++

### Why Sum for Bias vs Dot Product for Weights

+++

**Bias Gradient: Simple Sum**

For bias, every example contributes equally:
```
dJ_db = sum_over_all_examples(error * activation_derivative)
```

Why? Because bias affects **every example identically** - it's like a universal offset.

**Weight Gradient: Dot Product**

For weights, each example contributes **differently** based on its input features:
```
dJ_dw = dot_product(error * activation_derivative, x)
```

Why dot product? Let's break it down:

**Concrete Example**

Say we have 3 examples and 2 features:

```python
# Input data (3 examples, 2 features)
x = [[0.1, 0.2],    # example 1
     [0.3, 0.4],    # example 2  
     [0.5, 0.6]]    # example 3

# For each example:
errors = [0.5, -0.2, 0.3]                    # (y_pred - y_true)
derivatives = [1.0, 1.0, 1.0]                # activation derivatives

# Bias gradient (simple sum):
dJ_db = (0.5*1.0) + (-0.2*1.0) + (0.3*1.0) = 0.5 - 0.2 + 0.3 = 0.6

# Weight gradient (dot product):
# We need: sum over examples of (error * derivative * x_ij) for each feature j

# For weight w₁ (first feature):
dJ_dw1 = (0.5*1.0*0.1) + (-0.2*1.0*0.3) + (0.3*1.0*0.5) 
       = 0.05 + (-0.06) + 0.15 = 0.14

# For weight w₂ (second feature):  
dJ_dw2 = (0.5*1.0*0.2) + (-0.2*1.0*0.4) + (0.3*1.0*0.6)
       = 0.10 + (-0.08) + 0.18 = 0.20

dJ_dw = [0.14, 0.20]  # This is exactly what np.dot(error * derivative, x) computes!
```

**The Key Difference**

- **Bias**: Same "contribution weight" for every example (always ×1)
- **Weights**: Contribution depends on the input feature values

So we accumulate across examples for both, but **how** we accumulate differs:

- Bias: Simple sum (all examples treated equally)
- Weights: Weighted sum (examples weighted by their input features)

+++

## `self.forward` dependency problem

+++

```python
def gradient(self, X: np.array, y_true: np.array) -> np.array:
    """Gradients for squared error loss: J = (y_pred - y_true)^2."""
    error = self.a - y_true  # ← RELIES ON PREVIOUS forward() CALL!
```

**Problem**: `gradient()` depends on `self.a` being populated by a previous `forward()` call. This creates hidden state dependencies.

**Risk**: If someone calls `gradient()` without calling `forward()` first, they get stale or missing `self.a` values.

**Fix Options**:
- Option A: Call `forward()` internally within `gradient()`
- Option B: Require `y_pred` as parameter to `gradient()`
- Option C: Document the dependency clearly and add validation

How do you want to handle the state dependency between `forward()` and `gradient()`? This is the main architectural decision remaining.

Answer: "I decided to add self.forward to the self.gradient method. I do not like such approaches because one can call self.forward twice, but it looks like this is the standard engineering way so people know this works like this and if I do it in my style they may miss the documentation and be confused."

You've chosen the pragmatic, standard approach.

**Why This is the Right Choice**

1. **Principle of Least Surprise**: Most ML practitioners expect `gradient()` to be self-contained
2. **API Safety**: Prevents subtle bugs from incorrect call sequences  
3. **Standard Pattern**: Matches how frameworks like PyTorch and TensorFlow work internally
4. **Documentation Simplicity**: Reduces the cognitive load on users

**The Engineering Trade-off**

You correctly identified the trade-off:
- **Your preferred style**: Explicit dependencies, cleaner separation of concerns
- **Standard approach**: Implicit forward call, more robust for general use

In systems architecture, we often choose the **more robust** pattern over the **theoretically pure** one, especially for user-facing APIs.

**Performance Note**

Yes, this means `forward()` might be called twice if someone does:
```python
y = neuron.forward(X)
grads = neuron.gradient(X, y_true)  # forward() called again internally
```

But in practice:
- The computational cost is negligible for a single neuron
- The safety benefit outweighs the minor redundancy
- In training loops, you typically only call `gradient()` anyway

More over, this design is correct for the educational context. The forward pass within gradient computation ensures fresh state.

+++

# 2.3 Code updated

```{code-cell} ipython3
import numpy as np


class Neuron:
    """Implement single neuron class."""

    def __init__(self: "Neuron") -> None:
        """Initialize neuron entity."""
        self.w: np.ndarray = None
        self.b: np.float64 = np.float64(0.0)
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
```

```{code-cell} ipython3
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

# print("my_neuron.w:", my_neuron.w)
# print("linear transformation:", my_neuron._get_linear_transformation(X))
# print("my_neuron.forward(X):", my_neuron.forward(X))
print("weights:", my_neuron.w)
print("linear transformation:", my_neuron.z)
print("activation:", my_neuron.a)
print("dJ_dw:", dJ_dw)
print("dJ_db:", dJ_db)
```

## Type Hint Best Practices

+++

For deep learning systems:

```python
# Standard practice:
import numpy.typing as npt

class Neuron:
    def forward(
        self,
        X: npt.NDArray[np.float32],  # Consistent precision
        activation_f: str = "leaky_relu",
    ) -> npt.NDArray[np.float32]:
        
    # Use float32 throughout for GPU compatibility
    self.w: npt.NDArray[np.float32] = None  
    self.b: np.float32 = np.float32(0.0)
    self.lr: np.float32 = np.float32(0.01)
```

**Rationale:** GPUs are optimized for float32, and mixed precision causes unnecessary casting.

+++

# <b>3. Weights update</b>

+++

# 3.1 Update weights test oracle

+++

A **test oracle** - a separate, verified implementation used to validate your main code.

**Test Oracle Pattern**: Creating an independent implementation to verify the system under test. This is valid when:
- The oracle is simpler/more transparent than the main implementation
- It's manually verified by a human before use
- It serves as a reference implementation

**Your framework below is actually sophisticated**:
- It documents the complete mathematical reasoning
- Allows manual verification of each test case
- Creates reproducible, mathematically consistent scenarios
- Serves as both test data AND documentation

**When This Approach Is Valuable**

1. **Complex mathematical systems** (like neural networks)
2. **Learning contexts** where understanding the derivation matters
3. **Reference implementations** for algorithm validation
4. **Documentation of expected behavior**

**The Professional Balance**

In production, you'd likely:
- Keep your detailed oracle for complex cases
- Use simple manual tests for basic functionality
- Have both verification strategies

**Your approach is architecturally sound for a learning context**. The key is ensuring you manually verify the oracle outputs before using them to test your implementation.

```{code-cell} ipython3
import numpy as np

def create_backprop_test_case(case_name, X, y_true, w, b, lr, activation_f="leaky_relu", cost_f="mse",):
    """Create backpropagation test case."""
    # final result
    result = {
        "name": case_name,
        "initial_X": X,
        "y_true": y_true,
        "initial_w": w,
        "initial_b": b,
        "learning_rate": lr
    }

    # linear transformation
    z = np.dot(X, w) + b
    result["z"] = z
    
    # activation function
    alpha = 0.01
    if activation_f == "leaky_relu":
        a = np.maximum(z * alpha, z)
    result["a"] = a

    # cost function
    if cost_f == "mse":
        u = a - y_true
        J = u**2 / 2
    else:
        raise ValueError(f"Cost function \"{cost_function}\" is not implemented yet.")

    result["J"] = J

    # backpropagation
    
    # J'
    dJ_da = u
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

    dJ_db = np.sum(dJ_da * da_dz)*dz_b  # where dz_b = 1
    result["dJ_db"] = dJ_db

    # w - lr * (-gradient) = w + lr*|gradient|
    result["expected_w"] = np.subtract(w, (lr * dJ_dw))
    result["expected_b"] = np.subtract(b, (lr * dJ_db))

    return result
```

```{code-cell} ipython3
case1 = create_backprop_test_case(
    "negative_gradients_increase_weights",
     np.array([[1.0, -2.0]]),
     y_true = 1.5,
     w = np.array([0.3, 0.4]),
     b = 0.1,
     lr = 0.01
)
case1
```

Your gradient computation is now mathematically correct.

These gradients make perfect sense:
- The weight gradients are proportional to their input values (1.0 and 2.0)
- All gradients point downward (negative) since we need to increase the weights to reduce the loss

We now have mathematically consistent test data:
- Initial: `w = [0.3, 0.4]`, `b = 0.1`
- Gradients: `dJ_dw = [-0.6, -1.2]`, `dJ_db = [-0.6]`
- Learning rate: `0.01`

**Gradient Descent Update:**
```
w_new = w_old - learning_rate * gradient
```

If gradient is **negative**, then:
```
w_new = w_old - learning_rate * (negative_number)
w_new = w_old + learning_rate * positive_number
```

**In our case:**
- Gradients are all negative: `[-0.3, -0.6]` and `[-0.3]`
- This means we need to increase weights and bias to reduce loss

**Expected after update:**
```
w_new = [0.3, 0.4] - 0.01 * [-0.3, -0.6] = [0.303, 0.406]
b_new = 0.1 - 0.01 * [-0.3] = [0.103]
```

```{code-cell} ipython3
case1
```

Create more test cases:

```{code-cell} ipython3
# Edge case: Zero gradients (no learning should occur)
case2 = create_backprop_test_case(
    "zero_gradients_no_change",
    np.array([[1.0, 2.0]]),
    y_true=1.2,  # Exactly matches our forward pass output
    w=np.array([0.3, 0.4]),
    b=0.1,
    lr=0.01
)

# Edge case: Large learning rate
case3 = create_backprop_test_case(
    "large_learning_rate",
    np.array([[1.0, 2.0]]),
    y_true=2.0,  # Larger error
    w=np.array([0.3, 0.4]),
    b=0.1,
    lr=0.1  # 10x larger learning rate
)

# Batch input case (multiple examples)
case4 = create_backprop_test_case(
    "batch_input_gradients",
    np.array([[1.0, 2.0], [0.5, 1.0]]),  # 2 examples
    y_true=np.array([1.5, 0.8]),  # Batch targets
    w=np.array([0.3, 0.4]),
    b=0.1,
    lr=0.01
)

# Single feature case
case5 = create_backprop_test_case(
    "single_feature",
    np.array([[1.0]]),  # Single input feature
    y_true=0.5,
    w=np.array([0.3]),
    b=0.1,
    lr=0.01
)

# Extreme values case
case6 = create_backprop_test_case(
    "extreme_gradients",
    np.array([[100.0, 200.0]]),  # Large inputs
    y_true=500.0,  # Large target
    w=np.array([0.3, 0.4]),
    b=0.1,
    lr=0.001  # Smaller LR for stability
)

test_cases = [case1, case2, case3, case4, case5, case6]

test_cases
```

## Test Oracle Separation: Best Practices

+++

**Separate responsibilities:**

If your `Neuron.gradient()` has a bug, your test oracle won't have the same bug.

```python
def compute_expected_gradients(X, w, b, y_true, alpha=0.01):
    """Pure function: independent mathematical verification"""
    # Manual computation without Neuron class
    z = X @ w + b
    a = np.maximum(alpha * z, z)
    dJ_da = a - y_true
    da_dz = np.where(z < 0, alpha, 1.0)
    dJ_dw = (dJ_da * da_dz) @ X / X.shape[0]  # Note: batch average!
    dJ_db = np.sum(dJ_da * da_dz) / X.shape[0]
    return dJ_dw, dJ_db

class TestNeuron:
    def create_test_case(self, name, X, w, b, y_true):
        # Just store test parameters
        test_case = {"name": name, "X": X, "w": w, "b": b, "y_true": y_true}
        
        # Compute expected results independently
        expected_dw, expected_db = compute_expected_gradients(X, w, b, y_true)
        test_case["expected_dw"] = expected_dw
        test_case["expected_db"] = expected_db
        
        self.test_cases.append(test_case)
```

+++

# 3.2 TDD cycle

+++

We follow the TDD cycle: **Red** → **Green** → **Refactor**.

+++

## Current Phase: RED (Write Failing Test)

+++

Using your test oracle data:

```python
def test_weight_update_negative_gradients():
    """Test that negative gradients correctly increase weights."""
    neuron = Neuron()
    
    # Setup initial state from oracle
    neuron.w = np.array([0.3, 0.4])
    neuron.b = 0.1
    
    # Gradients from oracle calculation
    dJ_dw = np.array([-0.3, -0.6])
    dJ_db = -0.3
    learning_rate = 0.01
    
    # Call method (doesn't exist yet - this will fail)
    neuron.update_weights(dJ_dw, dJ_db, learning_rate)
    
    # Expected results from oracle
    expected_w = np.array([0.303, 0.406])
    expected_b = 0.103
    
    # Assertions (will fail initially)
    np.testing.assert_array_almost_equal(neuron.w, expected_w, decimal=6)
    assert abs(neuron.b - expected_b) < 1e-6
```

**Your turn**: This test will fail because `update_weights` doesn't exist yet. Should we:
1. Write this test and watch it fail (Red phase)
2. Then implement the minimal `update_weights` method to make it pass (Green phase)

*(I'll wait for your confirmation to proceed with the test)*
