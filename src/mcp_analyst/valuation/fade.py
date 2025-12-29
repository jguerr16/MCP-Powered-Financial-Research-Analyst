"""Fade schedule utilities for growth and margin projections."""

from typing import List


def linear_fade(start: float, end: float, n: int) -> List[float]:
    """
    Linear fade from start to end over n periods.
    
    Args:
        start: Starting value
        end: Ending value
        n: Number of periods
        
    Returns:
        List of n values fading linearly from start to end
    """
    if n <= 1:
        return [start]
    
    step = (end - start) / (n - 1)
    return [start + step * i for i in range(n)]


def exp_fade(start: float, end: float, n: int, k: float = 0.5) -> List[float]:
    """
    Exponential fade from start to end over n periods.
    
    Args:
        start: Starting value
        end: Ending value
        n: Number of periods
        k: Fade rate (higher = faster fade, default 0.5)
        
    Returns:
        List of n values fading exponentially from start to end
    """
    if n <= 1:
        return [start]
    
    result = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0
        # Exponential decay: start * (end/start)^(t^k)
        if start > 0 and end > 0:
            value = start * ((end / start) ** (t ** k))
        else:
            # Linear fallback if values are problematic
            value = start + (end - start) * t
        result.append(value)
    
    return result


def piecewise_fade(start: float, mid: float, end: float, n: int, split: int = 2) -> List[float]:
    """
    Piecewise fade: fast fade in first 'split' periods, slower fade thereafter.
    
    Args:
        start: Starting value
        mid: Midpoint value (after split periods)
        end: Ending value
        n: Total number of periods
        split: Number of periods for fast fade (default 2)
        
    Returns:
        List of n values with piecewise fade
    """
    if n <= 1:
        return [start]
    
    if split >= n:
        # All fast fade
        return linear_fade(start, end, n)
    
    result = []
    
    # Fast fade: start to mid over split periods
    fast_fade = linear_fade(start, mid, split)
    result.extend(fast_fade)
    
    # Slow fade: mid to end over remaining periods
    if n > split:
        slow_fade = linear_fade(mid, end, n - split)
        result.extend(slow_fade)
    
    return result


def get_fade_schedule(method: str, start: float, end: float, n: int, **kwargs) -> List[float]:
    """
    Get fade schedule based on method name.
    
    Args:
        method: "linear", "exp", or "piecewise"
        start: Starting value
        end: Ending value
        n: Number of periods
        **kwargs: Additional parameters (mid, split, k)
        
    Returns:
        List of faded values
    """
    if method == "linear":
        return linear_fade(start, end, n)
    elif method == "exp":
        k = kwargs.get("k", 0.5)
        return exp_fade(start, end, n, k)
    elif method == "piecewise":
        mid = kwargs.get("mid", (start + end) / 2)
        split = kwargs.get("split", 2)
        return piecewise_fade(start, mid, end, n, split)
    else:
        # Default to linear
        return linear_fade(start, end, n)

