def load_data(file_path):
    with open(file_path, 'r') as file:
        data = file.read()
    return data

def preprocess_data(data):
    # Example preprocessing: convert to lowercase and split into words
    processed_data = data.lower().split()
    return processed_data

def calculate_metrics(processed_data):
    word_count = len(processed_data)
    unique_words = set(processed_data)
    unique_word_count = len(unique_words)
    return word_count, unique_word_count

def main():
    file_path = 'data.txt'  # Path to your data file
    data = load_data(file_path)
    processed_data = preprocess_data(data)
    word_count, unique_word_count = calculate_metrics(processed_data)
    
    print(f'Total words: {word_count}')
    print(f'Unique words: {unique_word_count}') 


if __name__ == "__main__":
    main()