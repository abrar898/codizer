# O(1) - Constant time complexity
def constant_time_function(n):
    return n * 2

# O(n) - Linear time complexity
def linear_time_function(arr):
    total = 0
    for item in arr:
        total += item
    return total

# O(n^2) - Quadratic time complexity
def quadratic_time_function(arr):
    result = []
    for i in arr:
        for j in arr:
            result.append(i * j)
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

# O(n log n) - Linearithmic time complexity
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
        
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)
    
def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
            
    result.extend(left[i:])
    result.extend(right[j:])
    return result 