# import math

# def generalized_binomial(n, k):
#     num = 1
#     for i in range(k):
#         num *= (n - i)
#     return num / math.factorial(k)

# def binomial_series(n, x, terms=20):
#     s = 0
#     for k in range(terms):
#         s += generalized_binomial(n, k) * (x**k)
#     return s

# approx = binomial_series(0.5, 0.0001, terms=25)
# actual = math.sqrt(1.0001)

# print("Series approximation :", approx)
# print("math.sqrt(1.0001)    :", actual)



# We'll build the partial sums of (1 + x)^(1/2) for x=0.0001
# # using the binomial series.

# def binomial_coeff_half(k):
#     """
#     Returns the generalized binomial coefficient (1/2 choose k)
#     = [ (1/2)(1/2 - 1)(1/2 - 2)...(1/2 - (k-1)) ] / k!
#     """
#     import math
#     # For k=0, by definition choose = 1
#     if k == 0:
#         return 1.0
#     num = 1.0
#     for i in range(k):
#         num *= (0.5 - i)
#     denom = math.factorial(k)
#     return num / denom

# def sqrt_1_plus_x_binomial(x, terms=10):
#     """
#     Compute (1 + x)^(1/2) by summing the binomial series up to 'terms' terms.
#     """
#     s = 0.0
#     for k in range(terms):
#         s += binomial_coeff_half(k) * (x**k)
#     return s

# x = 0.0001
# approx = sqrt_1_plus_x_binomial(x, terms=12)  # 12 terms is likely plenty
# print(f"Approx. series sum = {approx:.18f}")


# import numpy as np
# import matplotlib.pyplot as plt
# import math

# def binomial_coeff(n, k):
#     """Compute the binomial coefficient C(n,k) for integer n >= k >= 0."""
#     # This works directly for integer n >= 0.
#     # For negative or fractional n, see the 'generalized_binomial' below.
#     from math import comb
#     return comb(n, k)  # Python 3.8+ has comb()

# def partial_sum_binomial(n, x_vals, num_terms=None):
#     """
#     Return partial sums of (1 + x)^n using the binomial series for integer n >= 0.
#     If n is an integer, the series actually terminates at k = n.
#     """
#     # If n is an integer, we only need up to k=n terms.
#     if num_terms is None:
#         num_terms = n + 1  # The series is finite in this case.

#     sums = []
#     for x in x_vals:
#         total = 0
#         for k in range(num_terms):
#             total += binomial_coeff(n, k) * (x**k)
#         sums.append(total)
#     return np.array(sums)

# # --- Main script ---
# x_vals = np.linspace(-0.9, 0.9, 200)  # Range within radius of convergence

# # Exact function for n=2
# exact = (1 + x_vals)**2

# # Partial sums: for n=2, the full expansion is just 1 + 2x + x^2
# # But let's pretend we do partial sums up to k=0, then k=1, then k=2
# p0 = partial_sum_binomial(2, x_vals, num_terms=1)  # 1 term => k=0
# p1 = partial_sum_binomial(2, x_vals, num_terms=2)  # 2 terms => k=0,1
# p2 = partial_sum_binomial(2, x_vals, num_terms=3)  # 3 terms => k=0,1,2

# plt.figure(figsize=(8,5))
# plt.plot(x_vals, exact, label='Exact: (1 + x)^2', color='black')
# plt.plot(x_vals, p0, '--', label='Partial sum k=0')
# plt.plot(x_vals, p1, '--', label='Partial sum k=0..1')
# plt.plot(x_vals, p2, '--', label='Partial sum k=0..2 (full)')
# plt.title("Comparison of (1 + x)^2 and Its Partial Sums")
# plt.xlabel("x")
# plt.ylabel("y")
# plt.legend()
# plt.grid(True)
# plt.show()



# import numpy as np
# import matplotlib.pyplot as plt
# import math

# def generalized_binomial(n, k):
#     """
#     Computes the generalized binomial coefficient for real n and integer k >= 0:
#     C(n, k) = n*(n-1)*...*(n-k+1) / k!
#     """
#     from math import factorial
#     numerator = 1.0
#     for i in range(k):
#         numerator *= (n - i)
#     return numerator / factorial(k)

# def binomial_series(n, x, max_k=5):
#     """
#     Return partial sum of (1 + x)^n up to k = max_k - 1.
#     """
#     total = 0.0
#     for k in range(max_k):
#         coeff = generalized_binomial(n, k)
#         total += coeff * (x**k)
#     return total

# # --- Main script ---
# x_vals = np.linspace(-0.9, 0.9, 300)
# exact_sqrt = (1 + x_vals)**0.5  # exact function

# # We'll compare partial sums with different numbers of terms
# p5  = [binomial_series(0.5, x,  5) for x in x_vals]  # up to k=4
# p10 = [binomial_series(0.5, x, 10) for x in x_vals]  # up to k=9
# p15 = [binomial_series(0.5, x, 15) for x in x_vals]  # up to k=14

# plt.figure(figsize=(8,5))
# plt.plot(x_vals, exact_sqrt, label='Exact: sqrt(1 + x)', color='black')
# plt.plot(x_vals, p5,  '--', label='Partial sum k=0..4')
# plt.plot(x_vals, p10, '--', label='Partial sum k=0..9')
# plt.plot(x_vals, p15, '--', label='Partial sum k=0..14')
# plt.title("Comparison of sqrt(1 + x) and its Binomial Series Partial Sums")
# plt.xlabel("x")
# plt.ylabel("y")
# plt.legend()
# plt.grid(True)
# plt.show()



# import numpy as np
# import matplotlib.pyplot as plt

# x_vals = np.linspace(-1, 1, 400)

# # a) sqrt(x)
# # We can only define sqrt(x) for x >= 0 in real numbers
# x_vals_nonneg = np.linspace(0, 1, 200)
# y_sqrt = np.sqrt(x_vals_nonneg)

# # b) |x|
# y_abs = np.abs(x_vals)

# # Plot sqrt(x) (0..1)
# plt.figure(figsize=(8,5))
# plt.plot(x_vals_nonneg, y_sqrt, label='sqrt(x)')
# plt.title("f(x) = sqrt(x), x >= 0")
# plt.xlabel("x")
# plt.ylabel("y")
# plt.grid(True)
# plt.legend()
# plt.show()

# # Plot |x| (-1..1)
# plt.figure(figsize=(8,5))
# plt.plot(x_vals, y_abs, label='|x|')
# plt.title("f(x) = |x|")
# plt.xlabel("x")
# plt.ylabel("y")
# plt.grid(True)
# plt.legend()
# plt.show()


import numpy as np
import matplotlib.pyplot as plt

def partial_sum_inv1plusx2(x_vals, max_k=5):
    """
    Returns partial sums for (1 + x^2)^(-1) up to k = max_k-1.
    The k-th term is (-1)^k x^(2k).
    """
    sums = []
    for x in x_vals:
        total = 0.0
        for k in range(max_k):
            total += ((-1)**k) * (x**(2*k))
        sums.append(total)
    return np.array(sums)

# --- Main script ---
x_vals = np.linspace(-0.9, 0.9, 300)
exact_inv = 1.0 / (1.0 + x_vals**2)

p5  = partial_sum_inv1plusx2(x_vals, max_k=5)   # k=0..4
p10 = partial_sum_inv1plusx2(x_vals, max_k=10)  # k=0..9
p20 = partial_sum_inv1plusx2(x_vals, max_k=20)  # k=0..19

plt.figure(figsize=(8,5))
plt.plot(x_vals, exact_inv, label='Exact: 1/(1 + x^2)', color='black')
plt.plot(x_vals, p5,  '--', label='Partial sum k=0..4')
plt.plot(x_vals, p10, '--', label='Partial sum k=0..9')
plt.plot(x_vals, p20, '--', label='Partial sum k=0..19')
plt.title("Comparison of 1/(1 + x^2) and Its Series Partial Sums")
plt.xlabel("x")
plt.ylabel("y")
plt.legend()
plt.grid(True)
plt.show()





# # Solve for the smallest n that satisfies the inequality
# import math

# tolerance = 0.5 * 10**(-8)
# x = 0.1

# n = 1  # Start checking from the first term
# while (x**(n+1)) / (n+1) >= tolerance:
#     n += 1
    
# print(n)



