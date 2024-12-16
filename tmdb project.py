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

genre_url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={API_KEY}&language=en-US"
genre_response = requests.get(genre_url)
if genre_response.status_code == 200:
    genres = genre_response.json()['genres']
    genre_mapping = {genre['id']: genre['name'] for genre in genres}
else:
    print(f"Error: {genre_response.status_code}")
    genre_mapping = {}

# Data Collection
# all_movies will end up filling up with each individual movie, and then turned to a dataframe
all_movies = []
# I chose the range of 1980-2024, since 44 years of movies seems adequete for general trends
for year in range(1980, 2024):  
    # API call for each year and pulls data
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}&language=en-US&primary_release_year={year}"
    response = requests.get(url)

    # Adds on basic important data that I would need from each movie
    if response.status_code == 200:
        movies = response.json().get('results', [])
        for movie in movies:
            all_movies.append({
                'title': movie['title'],
                'genres': movie['genre_ids'],
                'popularity': movie.get('popularity'),
                'vote_average': movie.get('vote_average'),
                'release_year': year,
                'release_date': movie.get('release_date')
            })
    else:
        print(f"Error fetching data for year {year}: {response.status_code}")

# Preprocess Data
# Here I found that the genre(s) for each movie used ID numbers, so I had to use their API to map the ID to respective genres.
for movie in all_movies:
    movie['genres'] = [genre_mapping.get(genre_id, "Unknown") for genre_id in movie['genres']]

df = pd.DataFrame(all_movies)

# Exploding genres to create one row per genre per movie
df_exploded = df.explode('genres')

# Formatting of date month year quarter for future use of time data
df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')  # Convert to datetime, coercing errors
df['release_month'] = df['release_date'].dt.month  # Extract month (NaT will result in NaN)

df_exploded['release_month'] = df['release_month']
df_exploded['release_date'] = pd.to_datetime(df_exploded['release_date'], errors='coerce')
df_exploded['release_year'] = df_exploded['release_date'].dt.year
df_exploded['release_quarter'] = df_exploded['release_date'].dt.to_period('Q')

# 1. Genre Popularity Trends Over Time

class GenreQuarterlyTrends:
    def __init__(self, df, years=10):
        self.df = df_exploded
        self.years = years
        self.quarterly_data = None
        self.top_genres = None
        self.prepare_data()
        self.calculate_quarterly_trends()
    
    def prepare_data(self):
        # Filter for the last `n` years
        latest_year = self.df['release_year'].max()
        start_year = latest_year - (self.years - 1)
        self.df = self.df[(self.df['release_year'] >= start_year) & 
                          (self.df['release_year'] <= latest_year)]
    
    def calculate_quarterly_trends(self):
        # Group by genres and quarters
        grouped = self.df.groupby(['genres', 'release_quarter'])['popularity'].mean().reset_index()
        # Pivot for easier plotting
        self.quarterly_data = grouped.pivot_table(index='release_quarter',
                                                  columns='genres',
                                                  values='popularity',
                                                  fill_value=0)
        # Identify top 5 genres over the entire period
        genre_totals = self.quarterly_data.sum(axis=0)
        self.top_genres = genre_totals.sort_values(ascending=False).index[:5]
    
    def plot_trends(self):
        plt.figure(figsize=(14, 8))
        for genre in self.top_genres:
            plt.plot(self.quarterly_data.index.astype(str), 
                     self.quarterly_data[genre], label=genre)
        
        # Improve plot aesthetics
        plt.title(f"Quarterly Popularity Trends for Top 5 Genres Over the Last {self.years} Years")
        plt.xlabel("Quarter")
        plt.ylabel("Average Popularity")
        plt.xticks(rotation=45)
        plt.legend(title="Genres", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()


# Instantiate and use the class
quarterly_trends = GenreQuarterlyTrends(df, years=10)
quarterly_trends.plot_trends()

# 2. Ratings Per Genre
# Simple graphing that groups all the data by genre, and displays them in order of highest avg rating
genre_ratings = df_exploded.groupby(['genres'])['vote_average'].mean().sort_values(ascending=False)

plt.figure(figsize=(10, 6))
genre_ratings.plot(kind='bar', color='skyblue')
plt.title("Average Ratings by Genre")
plt.xlabel("Genre")
plt.ylabel("Average Rating")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# 3. Popularity vs. Quality (Vote Average vs. Popularity)
# Simple graphing that just uses all the data and plots relationship
plt.figure(figsize=(10, 6))
plt.scatter(df['popularity'], df['vote_average'], alpha=0.6, c='blue', edgecolors='w', s=50)
plt.title("Popularity vs Vote Average")
plt.xlabel("Popularity")
plt.ylabel("Vote Average")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# 4. Temporal Release Trends
class TemporalReleaseTrends:
    def __init__(self, df):
        self.df = df_exploded
        self.monthly_data = None
        self.top_genres = None
        self.aggregate_monthly_trends()

    def aggregate_monthly_trends(self):
        # Group by genres and release month, then count movies
        grouped = self.df.groupby(['genres', 'release_month']).size().unstack(fill_value=0)
        self.monthly_data = grouped
        # Identify top 5 genres by total movie count
        genre_totals = self.monthly_data.sum(axis=1)
        self.top_genres = genre_totals.sort_values(ascending=False).index[:5]

    def plot_trends(self):
        plt.figure(figsize=(14, 7))
        for genre in self.top_genres:
            plt.plot(self.monthly_data.columns, self.monthly_data.loc[genre], label=genre)
        
        # Plotting
        plt.title("Seasonal Trends for Top 5 Genres")
        plt.xlabel("Month")
        plt.ylabel("Number of Movies")
        plt.xticks(range(1, 13), labels=[
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]) 
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.show()

temporal_trends = TemporalReleaseTrends(df)
temporal_trends.plot_trends()

# 5. Year-over-Year Growth of Top Genres
# Calculating growth rates and sorting
genre_counts = df_exploded.groupby(['release_year', 'genres']).size().unstack(fill_value=0)
top_genres = genre_counts.iloc[-1].sort_values(ascending=False).head(5).index
growth_rates = genre_counts[top_genres].pct_change().fillna(0) * 100

plt.figure(figsize=(14, 7))

for genre in top_genres:
    plt.plot(growth_rates.index, growth_rates[genre], label=genre)
    top_peaks = growth_rates[genre].nlargest(3)
    
    # Annotate the peaks with year and percentage for better readability
    for year, value in top_peaks.items():
        plt.annotate(f'{year}: {value:.1f}%', 
                     xy=(year, value), 
                     xytext=(year, value + 10),
                     fontsize=8, ha='center', 
                     arrowprops=dict(arrowstyle='->', lw=0.5))

# Plotting
plt.title("Year-over-Year Growth Rate of Top Genres")
plt.xlabel("Year")
plt.ylabel("Growth Rate (%)")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
