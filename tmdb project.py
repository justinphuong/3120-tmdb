from key import API_KEY
from pip._vendor import requests
import pandas as pd
import matplotlib.pyplot as plt

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching details for movie ID {movie_id}: {response.status_code}")
        return None

url = f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=en-US&page=1"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    vote_counts = []
    revenues = []
    titles = []

    # Loop through popular movies
    for movie in data['results']:
        movie_id = movie['id']
        movie_details = get_movie_details(movie_id)
        
        if movie_details:
            vote_count = movie_details.get('vote_count', 0)
            revenue = movie_details.get('revenue', 0)  # Revenue may be 0 for unreleased movies
            title = movie_details.get('title', 'Unknown')

            # Collect data for analysis
            vote_counts.append(vote_count)
            revenues.append(revenue)
            titles.append(title)

    # Plot the data
    plt.figure(figsize=(8, 6))
    plt.scatter(vote_counts, revenues, color='blue', alpha=0.6)
    plt.title('Revenue vs. Vote Count')
    plt.xlabel('Vote Count')
    plt.ylabel('Revenue ($)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

else:
    print(f"Error: {response.status_code}")