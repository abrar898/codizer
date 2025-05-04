# O(1) - Constant time complexity


def constant_time(n):
    return n + 1

# O(n) - Linear time complexity
def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1

# O(n^2) - Quadratic time complexity
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

# O(n^3) - Cubic time complexity
def triple_nested_loop(n):
    result = 0
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result += 1
    return result

# O(log n) - Logarithmic time complexity
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

if __name__ == "__main__":
    # Test the functions
    my_array = [11, 12, 22, 25, 34, 64, 90]
    print(f"Constant time: {constant_time(5)}")
    print(f"Linear search for 12: {linear_search(my_array, 12)}")
    print(f"Binary search for 12: {binary_search(my_array, 12)}")
    print(f"Triple nested loop result: {triple_nested_loop(3)}")
    
    unsorted = [64, 34, 25, 12, 22, 11, 90]
    sorted_arr = bubble_sort(unsorted.copy())
    print(f"Bubble sort: {sorted_arr}") 