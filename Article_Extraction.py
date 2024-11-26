import pandas as pd
import requests,os, re, nltk
from bs4 import BeautifulSoup
from nltk.corpus import stopwords

# Load the file
input_file = "Input.xlsx"
data = pd.read_excel(input_file)

def get_article_content(url):
    try:
        response = requests.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.find('title').text if soup.find('title') else "No Title Found"

        # Extracting all paragraph text
        paragraphs = soup.find_all('p')
        article_body = ""
        for p in paragraphs:
            article_body += p.get_text() + " "

        return title, article_body.strip()

    except Exception as e:
        print("Error occurred while processing:", url, "->", e)
        return None, None


if not os.path.exists('extracted_articles'):
    os.makedirs('extracted_articles')

for index, row in data.iterrows():
    url_id = row['URL_ID']
    url = row['URL']

    article_title, article_text = get_article_content(url)

    if article_title and article_text:
        filename = f'extracted_articles/{url_id}.txt'
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(f"Title: {article_title}\n")
            file.write(article_text)
        print(f"Article {url_id} saved successfully.")
    else:
        print(f"Failed to extract article {url_id}.")

print("Data extraction finished.")


# Loading positive and negative words into lists
try:
    with open('positive-words.txt', 'r') as pos_file:
        positive_words = set(pos_file.read().split())
except FileNotFoundError:
    print("positive-words.txt file not found. Please ensure it's in the correct directory.")

try:
    with open('negative-words.txt', 'r') as neg_file:
        negative_words = set(neg_file.read().split())
except FileNotFoundError:
    print("negative-words.txt file not found. Please ensure it's in the correct directory.")

stop_words = set(stopwords.words('english'))



def clean_text(text):
    text = re.sub(r'\W', ' ', text)
    text = text.lower()

    # Basic tokenization using split (instead of nltk.word_tokenize)
    words = text.split()

    # Remove stop words
    cleaned_words = [word for word in words if word not in stop_words]
    return cleaned_words



def count_syllables(word):
    word = word.lower()
    syllables = re.findall(r'[aeiouy]+', word)  # Counting vowel groups as syllables
    return len(syllables)


# Function to analyze text and calculate metrics
def analyze_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    cleaned_words = clean_text(content)
    total_words = len(cleaned_words)

    # Calculate scores
    positive_count = sum(1 for word in cleaned_words if word in positive_words)
    negative_count = sum(1 for word in cleaned_words if word in negative_words)

    polarity = (positive_count - negative_count) / (positive_count + negative_count + 0.000001)
    subjectivity = (positive_count + negative_count) / (total_words + 0.000001)

    # Simple sentence splitting using periods
    sentences = content.split('.')
    avg_sentence_length = total_words / len(sentences) if len(sentences) > 0 else 0

    # Calculate complex words
    complex_words = [word for word in cleaned_words if len(re.findall(r'[aeiouy]+', word)) > 2]
    complex_count = len(complex_words)
    percent_complex = complex_count / total_words if total_words > 0 else 0

    # Calculate Fog Index
    fog_index = 0.4 * (avg_sentence_length + percent_complex)

    # Personal pronouns count
    pronouns = re.findall(r'\b(I|we|my|ours|us)\b', content, re.IGNORECASE)
    pronoun_count = len(pronouns)

    # Syllable count
    syllable_count = sum(count_syllables(word) for word in cleaned_words)

    # Average word length
    avg_word_length = sum(len(word) for word in cleaned_words) / total_words if total_words > 0 else 0

    return {
        "URL_ID": os.path.basename(file_path).split('.')[0],  # Extract URL_ID from filename
        "URL": "",  # Placeholder for URL (if needed)
        "Total Words": total_words,
        "Positive Score": positive_count,
        "Negative Score": negative_count,
        "Polarity Score": polarity,
        "Subjectivity Score": subjectivity,
        "Avg Sentence Length": avg_sentence_length,
        "Percentage of Complex Words": percent_complex,
        "Fog Index": fog_index,
        "Complex Word Count": complex_count,
        "Syllable Count": syllable_count,
        "Personal Pronouns": pronoun_count,
        "Avg Word Length": avg_word_length
    }


input_dir = "extracted_articles"

results = []

# Loop through each text file in the directory
for filename in os.listdir(input_dir):
    if filename.endswith('.txt'):
        file_path = os.path.join(input_dir, filename)
        metrics = analyze_text(file_path)
        metrics['URL'] = ""  # Optionally add the actual URL if available
        results.append(metrics)

df = pd.DataFrame(results)

columns_order = [
    'URL_ID', 'URL', 'Positive Score', 'Negative Score', 'Polarity Score',
    'Subjectivity Score', 'Avg Sentence Length', 'Percentage of Complex Words',
    'Fog Index', 'Complex Word Count', 'Total Words', 'Syllable Count',
    'Personal Pronouns', 'Avg Word Length'
]
df = df[columns_order]

output_file = "output_results.csv"
df.to_csv(output_file, index=False)

print(f"Results have been saved to {output_file}.")
