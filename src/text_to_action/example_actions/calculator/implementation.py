import math
from typing import Union, List
import numpy as np

def add(values: List[int]) -> int:
    """
    Returns the sum of a list of integers.
    """
    return sum(values)

def subtract(a: int, b: int) -> int:
    """
    Returns the difference between a and b.
    """
    return a - b

def multiply(values: List[int]) -> int:
    """
    Returns the product of a list of integers.
    """
    return np.prod(values)

def divide(a: float, b: float) -> Union[float, str]:
    """
    Returns the quotient of a divided by b.
    """
    if b == 0:
        return "Error: Division by zero"
    return a / b

def square_root(a: float) -> Union[float, str]:
    """
    Returns the square root of a.
    """
    if a < 0:
        return "Error: Negative input for square root"
    return math.sqrt(a)

def percentage(part: float, whole: float) -> Union[float, str]:
    """
    Returns the percentage of part with respect to whole.
    """
    if whole == 0:
        return "Error: Whole is zero"
    return (part / whole) * 100

def sine(x: float) -> float:
    """
    Returns the sine of x (x in radians).
    """
    return math.sin(x)

def cosine(x: float) -> float:
    """
    Returns the cosine of x (x in radians).
    """
    return math.cos(x)

def tangent(x: float) -> float:
    """
    Returns the tangent of x (x in radians).
    """
    return math.tan(x)

def inverse_sine(x: float) -> Union[float, str]:
    """
    Returns the inverse sine (arcsin) of x.
    """
    if x < -1 or x > 1:
        return "Error: Input out of range for arcsin"
    return math.asin(x)

def inverse_cosine(x: float) -> Union[float, str]:
    """
    Returns the inverse cosine (arccos) of x.
    """
    if x < -1 or x > 1:
        return "Error: Input out of range for arccos"
    return math.acos(x)

def inverse_tangent(x: float) -> float:
    """
    Returns the inverse tangent (arctan) of x.
    """
    return math.atan(x)

def natural_log(x: float) -> Union[float, str]:
    """
    Returns the natural logarithm (ln) of x.
    """
    if x <= 0:
        return "Error: Non-positive input for ln"
    return math.log(x)

def common_log(x: float) -> Union[float, str]:
    """
    Returns the common logarithm (log base 10) of x.
    """
    if x <= 0:
        return "Error: Non-positive input for log base 10"
    return math.log10(x)

def exponential(x: float) -> float:
    """
    Returns e raised to the power of x.
    """
    return math.exp(x)

def power(x: float, y: float) -> float:
    """
    Returns x raised to the power of y.
    """
    return math.pow(x, y)

def factorial(n: int) -> Union[int, str]:
    """
    Returns the factorial of n.
    """
    if n < 0:
        return "Error: Factorial of negative number"
    return math.factorial(n)

def sinh(x: float) -> float:
    """
    Returns the hyperbolic sine of x.
    """
    return math.sinh(x)

def cosh(x: float) -> float:
    """
    Returns the hyperbolic cosine of x.
    """
    return math.cosh(x)

def tanh(x: float) -> float:
    """
    Returns the hyperbolic tangent of x.
    """
    return math.tanh(x)

def inverse_sinh(x: float) -> float:
    """
    Returns the inverse hyperbolic sine (arsinh) of x.
    """
    return math.asinh(x)

def inverse_cosh(x: float) -> Union[float, str]:
    """
    Returns the inverse hyperbolic cosine (arcosh) of x.
    """
    if x < 1:
        return "Error: Input less than 1 for arcosh"
    return math.acosh(x)

def inverse_tanh(x: float) -> Union[float, str]:
    """
    Returns the inverse hyperbolic tangent (artanh) of x.
    """
    if x <= -1 or x >= 1:
        return "Error: Input out of range for artanh"
    return math.atanh(x)

def degrees_to_radians(degrees: float) -> float:
    """
    Converts degrees to radians.
    """
    return math.radians(degrees)

def radians_to_degrees(radians: float) -> float:
    """
    Converts radians to degrees.
    """
    return math.degrees(radians)

def reciprocal(x: float) -> Union[float, str]:
    """
    Returns the reciprocal of x.
    """
    if x == 0:
        return "Error: Division by zero"
    return 1 / x

def modulus(a: float, b: float) -> Union[float, str]:
    """
    Returns the modulus of a and b.
    """
    if b == 0:
        return "Error: Division by zero"
    return a % b

def absolute_value(x: float) -> float:
    """
    Returns the absolute value of x.
    """
    return abs(x)

def pi() -> float:
    """
    Returns the value of pi (π).
    """
    return math.pi

def mean(data: List[float]) -> float:
    """
    Returns the mean of the data.
    """
    return np.mean(data)

def median(data: List[float]) -> float:
    """
    Returns the median of the data.
    """
    return np.median(data)

def standard_deviation(data: List[float]) -> float:
    """
    Returns the standard deviation of the data.
    """
    return np.std(data)

def variance(data: List[float]) -> float:
    """
    Returns the variance of the data.
    """
    return np.var(data)

def scientific_constant(name: str) -> Union[float, str]:
    """
    Returns the value of a commonly used scientific constant.
    """
    constants = {
        'speed_of_light': 299792458,  # in meters per second
        'gravitational_constant': 6.67430e-11,  # in m^3 kg^-1 s^-2
        'planck_constant': 6.62607015e-34,  # in Js
        'boltzmann_constant': 1.380649e-23,  # in J/K
        'avogadro_constant': 6.02214076e23,  # in mol^-1
        'gas_constant': 8.314462618,  # in J/(mol·K)
        'electron_charge': 1.602176634e-19  # in coulombs
    }
    return constants.get(name.lower(), "Error: Unknown constant")

def permutations(n: int, k: int) -> int:
    """Calculate the number of permutations of n items taken r at a time."""
    if k > n:
        return 0
    return math.factorial(n) // math.factorial(n - k)

def combinations(n: int, k: int) -> int:
    """Calculate the number of combinations of n items taken r at a time."""
    if k > n:
        return 0
    return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))