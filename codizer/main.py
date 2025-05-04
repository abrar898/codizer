import os
import sys
import subprocess
import time
import json

# Main function and algorithm demonstrations
def main():
    # Test arrays
    my_array = [11, 12, 22, 25, 34, 64, 90]
    unsorted = [64, 34, 25, 12, 22, 11, 90]
    
    # Print algorithm results
    print(f"Constant time: {constant_time(5)}")
    print(f"Linear search for 12: {linear_search(my_array, 12)}")
    print(f"Binary search for 12: {binary_search(my_array, 12)}")
    print(f"Triple nested loop result: {triple_nested_loop(3)}")
    
    print(f"Original array: {unsorted}")
    print(f"Bubble sort: {bubble_sort(unsorted.copy())}")
    print(f"Merge sort: {merge_sort(unsorted.copy())}")
    
    # Test n value
    n = 15
    print("Counting from 15 to 20:")
    while n <= 20:  # O(1) - only iterates 6 times
        print(n)
        n += 1

# Time Complexity: O(1)
# Space Complexity: O(1)
def constant_time(n):
    return n + 1  # Simple arithmetic operation: O(1)

# Time Complexity: O(n)
# Space Complexity: O(1)
def linear_search(arr, target):
    # Single loop through array of length n: O(n)
    for i in range(len(arr)):  # O(n)
        if arr[i] == target:   # O(1)
            return i           # O(1)
    return -1                  # O(1)

# Time Complexity: O(n^2)
# Space Complexity: O(1)
def bubble_sort(arr):
    n = len(arr)               # O(1)
    # Two nested loops: outer O(n), inner O(n) → O(n²)
    for i in range(n):         # O(n)
        for j in range(0, n - i - 1):  # O(n)
            if arr[j] > arr[j + 1]:    # O(1)
                arr[j], arr[j + 1] = arr[j + 1], arr[j]  # O(1)
    return arr                 # O(1)

# Time Complexity: O(n^3)
# Space Complexity: O(1)
def triple_nested_loop(n):
    result = 0                 # O(1)
    # Three nested loops: O(n³)
    for i in range(n):         # O(n)
        for j in range(n):     # O(n)
            for k in range(n): # O(n)
                result += 1    # O(1)
    return result              # O(1)

# Time Complexity: O(log n)
# Space Complexity: O(1)
def binary_search(arr, target):
    left, right = 0, len(arr) - 1  # O(1)
    
    # Loop divides search space in half each time: O(log n)
    while left <= right:       # O(log n)
        mid = (left + right) // 2  # O(1)
        if arr[mid] == target:     # O(1)
            return mid             # O(1)
        elif arr[mid] < target:    # O(1)
            left = mid + 1         # O(1)
        else:
            right = mid - 1        # O(1)
    
    return -1                  # O(1)

# Time Complexity: O(n log n)
# Space Complexity: O(n)
def merge_sort(arr):
    if len(arr) <= 1:          # O(1)
        return arr             # O(1)
    
    # Divide the array into two halves
    mid = len(arr) // 2        # O(1)
    # Recursive calls: T(n) = 2T(n/2) + O(n) → O(n log n)
    left_half = merge_sort(arr[:mid])   # T(n/2)
    right_half = merge_sort(arr[mid:])  # T(n/2)
    
    # Merge step takes O(n)
    return merge(left_half, right_half) # O(n)

# Time Complexity: O(n)
# Space Complexity: O(n)
def merge(left, right):
    result = []                # O(1)
    i = j = 0                  # O(1)
    
    # Linear time to merge two arrays: O(n)
    while i < len(left) and j < len(right):  # O(n)
        if left[i] <= right[j]:    # O(1)
            result.append(left[i])  # O(1)
            i += 1                  # O(1)
        else:
            result.append(right[j]) # O(1)
            j += 1                  # O(1)
    
    # These operations are at most O(n)
    result.extend(left[i:])    # O(n)
    result.extend(right[j:])   # O(n)
    return result              # O(1)

if __name__ == "__main__":
    main()