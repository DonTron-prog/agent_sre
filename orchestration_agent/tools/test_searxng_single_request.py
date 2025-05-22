import asyncio
import aiohttp
import json

# Configuration
SEARXNG_BASE_URL = "http://localhost:8080"  # Adjust if your SearXNG is on a different URL/port
TEST_QUERY = "test query"
TEST_CATEGORY = "general" # Optional: "general", "news", "social_media"

async def test_searxng_single_request():
    """
    Sends a single search request to SearXNG and prints the response.
    """
    query_params = {
        "q": TEST_QUERY,
        "safesearch": "0",
        "format": "json",
        "language": "en",
        "engines": "duckduckgo", # Using a single engine for simplicity
    }

    if TEST_CATEGORY:
        query_params["categories"] = TEST_CATEGORY

    target_url = f"{SEARXNG_BASE_URL}/search"
    print(f"Attempting to send a single request to: {target_url}")
    print(f"With parameters: {query_params}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(target_url, params=query_params, timeout=100) as response: # headers are now part of the session
                print(f"\n--- Request Headers ---")
                for key, value in response.request_info.headers.items(): # Still useful to print the actual sent headers
                    print(f"{key}: {value}")
                
                print(f"\n--- Response ---")
                print(f"Status Code: {response.status}")
                print(f"Reason: {response.reason}")
                
                response_text = await response.text()
                
                print(f"\nRaw Response Text (first 500 chars):")
                print(response_text[:500])

                if response.status == 200:
                    try:
                        data = json.loads(response_text) # Manually parse if content-type is not ideal
                        print(f"\nParsed JSON Response:")
                        print(json.dumps(data, indent=2))
                        
                        if "results" in data and data["results"]:
                            print(f"\nFound {len(data['results'])} results.")
                            print("First result:")
                            print(json.dumps(data["results"][0], indent=2))
                        elif "results" in data:
                            print("\nNo results found in the response.")
                        else:
                            print("\n'results' key not found in JSON response.")
                            
                    except json.JSONDecodeError:
                        print("\nFailed to parse response as JSON.")
                else:
                    print("\nRequest failed or returned non-200 status.")

        except aiohttp.ClientConnectorError as e:
            print(f"\nConnection Error: Could not connect to {target_url}.")
            print(f"Details: {e}")
        except asyncio.TimeoutError:
            print(f"\nTimeout Error: The request to {target_url} timed out after 10 seconds.")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    print("Running SearXNG Single Request Test Script...")
    asyncio.run(test_searxng_single_request())