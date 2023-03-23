# Import MP-SPDZ libraries
from Compiler.ml import relu
from Compiler.util import max, min, mod2m, if_else
from Compiler import ml
from Compiler.mpc_math import *
from Compiler.library import *

# Define the number of parties and dimensions
n_parties = 3 # Three parties: P0, P1 and P2
n_dims = 5 # Five dimensions: x1, x2, x3, x4 and x5

# Define the input data for each party
# Each party inputs a secret-shared vector of length n_dims + 1
# The last element is the label (y) for P2 and a dummy value (0) for P0 and P1
x0 = [sint(1), sint(2), sint(0), sint(0), sint(0), sint(0)] # P0 inputs x1 and x2
x1 = [sint(0), sint(0), sint(3), sint(4), sint(5), sint(0)] # P1 inputs x3, x4 and x5
x2 = [sint(0), sint(0), sint(0), sint(0), sint(0), sint(-1)] # P2 inputs y

# Define the parameters for SVM training
C = 10 # Regularization parameter
T = 100 # Number of iterations
eta = 1e-3 # Learning rate

# Initialize the weight vector (w) and bias term (b) randomly
w = [sfix.get_random(-1, 1) for _ in range(n_dims)] # w is a public vector of length n_dims
b = sfix.get_random(-1, 1) # b is a public scalar

# Define a function to compute the dot product of two vectors securely
def dot_product(x, y):
    assert len(x) == len(y)
    result = cfix.Array(len(x))
    @for_range(len(x))
    def _(i):
        result[i] = x[i] * y[i]
    return sum(result)

# Define a function to compute the hinge loss securely
def hinge_loss(w, b, x, y):
    z = dot_product(w, x) + b # Linear combination of w and x plus b
    return relu(cfix.Array([C - y * z]))[0] # ReLU(C - y * z)

# Define a function to update the weight vector and bias term securely using gradient descent
def update(w, b, x, y):
    z = dot_product(w,x) + b # Linear combination of w and x plus b
    g_w = cfix.Array(n_dims) # Gradient of w
    g_b = cfix.Array([y * (z - C)])[0] if z > C else cfix.Array([y * z])[0] if z < 0 else cfix.Array([if_else(z < C / 2. , -y * C / 2., y * C / 2.)])[0]   # Gradient of b
    @for_range(n_dims)
    def _(i):
        g_w[i] = if_else(z > C , -y * x[i], -y * z * x[i]) if z < 0 else if_else(z < C / 2., -y * C / 2. *x[i], y * C / 2. *x[i])   # Conditional gradient computation
        w[i] -= eta * g_w[i]   # Update w using gradient descent
    b -= eta * g_b   # Update b using gradient descent

# Train the SVM model using the input data from all parties
@for_range(T)
def _(t):
    update(w,b,x,y)

# Print the final weight vector and bias term
print_ln("w: %s", str(w))
print_ln("b: %s", str(b))