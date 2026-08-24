import os
import pandas as pd
from pymongo import MongoClient

# MongoDB setup (edit if needed)
client = MongoClient("mongodb://localhost:27017/")
db = client["aesthetic"]  # Change to your MongoDB database name
collection = db["criticism"]  # Change to your MongoDB collection name

# Directory where the CSV files are located
directory = "./"  # Update this path

# Loop through each file in the directory
for filename in os.listdir(directory):
	if filename.endswith("_gale.csv"):
		# Extract category from the filename
		category = filename.split("_")[0]  # Gets 'Art', 'Concerts', etc.

		# Load CSV file into a DataFrame
		file_path = os.path.join(directory, filename)
		data = pd.read_csv(file_path)

		# Add the category column
		data["Category"] = category
		data["Source"] = "Gale"

		# Convert DataFrame to dictionary and insert into MongoDB
		records = data.to_dict(orient="records")
		collection.insert_many(records)
		print(f"Inserted records from {filename} into MongoDB")

client.close()
