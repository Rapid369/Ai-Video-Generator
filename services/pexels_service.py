import os
import re
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PexelsService:
    """Service for interacting with the Pexels API to find and download stock videos."""
    
    def __init__(self):
        """Initialize the Pexels service with API key from environment variables."""
        self.api_key = os.getenv("PEXELS_API_KEY")
        if not self.api_key:
            print("Warning: No Pexels API key found in environment variables.")
    
    def search_stock_videos(self, query, per_page=10, page=1):
        """
        Search for royalty-free stock videos using Pexels API.
        
        Args:
            query (str): The search query
            per_page (int): Number of results per page
            page (int): Page number for pagination
            
        Returns:
            list: List of video objects with details
        """
        print(f"Searching for stock videos with query: {query}")
        
        # Process query and remove special characters
        query = re.sub(r'[^\w\s]', ' ', query).strip()
        
        # Enhance the query for better results
        enhanced_query = f"{query} cinematic"
        
        # Search videos from Pexels API
        url = "https://api.pexels.com/videos/search"
        headers = {
            "Authorization": self.api_key
        }
        params = {
            "query": enhanced_query,
            "orientation": "landscape",
            "size": "medium",
            "per_page": per_page,
            "page": page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            videos = response.json().get("videos", [])
            
            # Process results and return formatted data
            result = []
            for video in videos:
                # Find the best quality file
                best_file = None
                for file in video.get("video_files", []):
                    if file.get("quality") == "hd" and file.get("file_type") == "video/mp4":
                        best_file = file
                        break
                
                if not best_file and video.get("video_files"):
                    best_file = video["video_files"][0]
                
                if best_file:
                    result.append({
                        "id": video.get("id"),
                        "url": best_file.get("link", ""),
                        "preview_url": video.get("image", ""),
                        "duration": video.get("duration", 10),
                        "width": best_file.get("width", 1280),
                        "height": best_file.get("height", 720)
                    })
            
            return result
        except Exception as e:
            print(f"Error searching for stock videos: {str(e)}")
            return []
    
    def download_stock_video(self, video_url, output_path):
        """
        Download a stock video from Pexels.
        
        Args:
            video_url (str): URL of the video to download
            output_path (str): Path where the video should be saved
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        print(f"Downloading stock video from: {video_url}")
        
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Download the video
            response = requests.get(video_url, stream=True, timeout=15)
            response.raise_for_status()
            
            # Save to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify file size to check for errors
            file_size = os.path.getsize(output_path)
            if file_size < 10000:  # File too small, likely corrupted
                os.remove(output_path)
                raise Exception("Downloaded file is too small")
            
            print(f"Stock video downloaded to: {output_path}")
            return True
        except Exception as e:
            print(f"Error downloading stock video: {str(e)}")
            return False
