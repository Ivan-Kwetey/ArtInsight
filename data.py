import requests
import json


# Function to fetch artworks with a generic query
def fetch_artworks(count=10):
    artworks_url = f'https://api.wikiart.org/v1/Artworks?count={count}'
    response = requests.get(artworks_url)

    if response.status_code == 200:
        artworks = response.json()
        if artworks:
            return artworks
        else:
            print("No artworks found.")
            return []
    else:
        print(f"Failed to fetch artworks, Status Code: {response.status_code}")
        print(f"Error Response: {response.text}")
        return []


# Collect data with the new query function
def collect_artworks_data():
    all_artworks_data = []
    artworks = fetch_artworks()  # No style filtering for now

    if artworks:
        for artwork in artworks:
            data = {
                'title': artwork['title'],
                'artist': artwork['artist'],
                'art_style': artwork.get('style', 'Unknown'),
                'image_url': artwork['imageUrl'],
                'year': artwork.get('year', 'Unknown'),
                'description': artwork.get('description', 'No description available'),
            }
            all_artworks_data.append(data)

    return all_artworks_data


# Save the collected data into a JSON file
def save_artworks_data_to_file(data, filename='artworks_data.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")


# Main function to run the script
if __name__ == '__main__':
    artworks_data = collect_artworks_data()
    save_artworks_data_to_file(artworks_data)
