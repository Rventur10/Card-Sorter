import re

# Function to extract the percentage value from a line
def extract_psa10_percentage(line):
    match = re.search(r'PSA 10: [\d.]+ \(([\d.]+)%\)', line)
    if match:
        return float(match.group(1))
    return 0.0

# Merge function for merge sort
def merge(left, right, left_percentages, right_percentages):
    sorted_list = []
    sorted_percentages = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left_percentages[i] > right_percentages[j]:
            sorted_list.append(left[i])
            sorted_percentages.append(left_percentages[i])
            i += 1
        else:
            sorted_list.append(right[j])
            sorted_percentages.append(right_percentages[j])
            j += 1
    
    while i < len(left):
        sorted_list.append(left[i])
        sorted_percentages.append(left_percentages[i])
        i += 1
    
    while j < len(right):
        sorted_list.append(right[j])
        sorted_percentages.append(right_percentages[j])
        j += 1

    return sorted_list, sorted_percentages

# Merge sort function
def merge_sort(lines, percentages):
    if len(lines) <= 1:
        return lines, percentages
    
    mid = len(lines) // 2
    left_half, left_percentages = merge_sort(lines[:mid], percentages[:mid])
    right_half, right_percentages = merge_sort(lines[mid:], percentages[mid:])
    
    return merge(left_half, right_half, left_percentages, right_percentages)

def main():
    with open("ebay_card_data.txt", "r") as input_file:
        cards = input_file.readlines()

    # Extract percentages once
    percentages = [extract_psa10_percentage(card) for card in cards]

    # Sort the lines using merge sort
    sorted_cards, _ = merge_sort(cards, percentages)

    # Write the sorted lines back to the file (or to a new file)
    with open("sorted_ebay_card_data.txt", "w") as output_file:
        output_file.writelines(sorted_cards)

if __name__ == "__main__":
    main()
