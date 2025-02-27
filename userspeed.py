import re
import requests
from difflib import SequenceMatcher
from termcolor import colored
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
from PIL import Image
import io
ascii_art = """
▄• ▄▌.▄▄ · ▄▄▄ .▄▄▄  .▄▄ ·  ▄▄▄·▄▄▄ .▄▄▄ .·▄▄▄▄  
█▪██▌▐█ ▀. ▀▄.▀·▀▄ █·▐█ ▀. ▐█ ▄█▀▄.▀·▀▄.▀·██▪ ██ 
█▌▐█▌▄▀▀▀█▄▐▀▀▪▄▐▀▀▄ ▄▀▀▀█▄ ██▀·▐▀▀▪▄▐▀▀▪▄▐█· ▐█▌
▐█▄█▌▐█▄▪▐█▐█▄▄▌▐█•█▌▐█▄▪▐█▐█▪·•▐█▄▄▌▐█▄▄▌██. ██ 
 ▀▀▀  ▀▀▀▀  ▀▀▀ .▀  ▀ ▀▀▀▀ .▀    ▀▀▀  ▀▀▀ ▀▀▀▀▀•                                                                                                
"""
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def extract_links(text):
    return re.findall(r'https?://\S+', text) if text else []


def show_instagram_images(image_urls):
    for url in image_urls:
        response = requests.get(url)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            image.show()  

def get_instagram_profile(username):
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/537.36",
        "X-IG-App-ID": "936619743392459"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return {
            "Platform": "Instagram",
            "Username": username,
            "Full Name": colored("Profile not found", "red"),
            "Bio": colored("Profile not found", "red"),
            "Followers": colored("Profile not found", "red"),
            "Following": colored("Profile not found", "red"),
            "External Link": colored("Profile not found", "red"),
            "Detected Emails": [],
            "Detected Phone Numbers": [],
            "Private Account": colored("Profile not found", "red"),
            "Number of Posts": colored("Profile not found", "red"),
            "Stories Available": colored("Profile not found", "red"),
            "Recent Posts": colored("Profile not found", "red"),
            "Confidence Score": 0
        }
    
    data = response.json()
    user_info = data.get("data", {}).get("user", {})
    full_name = user_info.get("full_name", "N/A")
    is_private = user_info.get("is_private", False)
    num_posts = user_info.get("edge_owner_to_timeline_media", {}).get("count", 0)
    num_stories = user_info.get("highlight_reel_count", 0) if not is_private else "N/A"
    confidence = 30 if username.lower() in user_info.get("username", "").lower() else 0
    confidence += 20 if user_info.get("edge_followed_by", {}).get("count", 0) > 10 else 0
    confidence += 30 if user_info.get("external_url") else 0
    
    posts = []
    if not is_private:
        edges = user_info.get("edge_owner_to_timeline_media", {}).get("edges", [])
        for edge in edges:
            post_url = edge.get("node", {}).get("display_url", "N/A")
            posts.append(post_url)
    
    return {
        "Platform": "Instagram",
        "Username": username,
        "Full Name": full_name,
        "Bio": user_info.get("biography", "N/A"),
        "Followers": user_info.get("edge_followed_by", {}).get("count", 0),
        "Following": user_info.get("edge_follow", {}).get("count", 0),
        "External Link": user_info.get("external_url", "None"),
        "Detected Emails": re.findall(r'[\w\.-]+@[\w\.-]+', user_info.get("biography", "")),
        "Detected Phone Numbers": re.findall(r'\+?\d{10,15}', user_info.get("biography", "")),
        "Private Account": "Yes" if is_private else "No",
        "Number of Posts": num_posts,
        "Stories Available": num_stories,
        "Recent Posts": posts if not is_private else "N/A",
        "Confidence Score": confidence
    }
def get_twitter_profile(username):
    url = f"https://twitter.com/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return {
            "Platform": "Twitter",
            "Username": username,
            "Full Name": colored("Profile not found", "red"),
            "Bio": colored("Profile not found", "red"),
            "Followers": colored("Profile not found", "red"),
            "Following": colored("Profile not found", "red"),
            "Profile URL": colored("Profile not found", "red"),
            "External Links": [],
            "Confidence Score": 0
        }
    
    soup = BeautifulSoup(response.text, "html.parser")
    name_tag = soup.find("title")
    bio_tag = soup.find("meta", attrs={"name": "description"})
    full_name = name_tag.text.replace(" / X", "") if name_tag else "N/A"
    bio = bio_tag["content"] if bio_tag else "N/A"
    external_links = extract_links(bio) 
    confidence = 30 if username.lower() in url.lower() else 0
    confidence += 20 if similar(username, full_name) > 0.6 else 0
    
    return {
        "Platform": "Twitter",
        "Username": username,
        "Full Name": full_name,
        "Bio": bio,
        "Followers": "N/A (Login required)",
        "Following": "N/A (Login required)",
        "Profile URL": url,
        "External Links": external_links,
        "Confidence Score": confidence
    }


def get_github_profile(username):
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return {
            "Platform": "GitHub",
            "Username": username,
            "Full Name": colored("Profile not found", "red"),
            "Bio": colored("Profile not found", "red"),
            "Followers": colored("Profile not found", "red"),
            "Following": colored("Profile not found", "red"),
            "Profile URL": colored("Profile not found", "red"),
            "Blog/Links": [],
            "Company": colored("Profile not found", "red"),
            "Location": colored("Profile not found", "red"),
            "Public Repos": colored("Profile not found", "red"),
            "Created At": colored("Profile not found", "red"),
            "Twitter": colored("Profile not found", "red"),
            "Confidence Score": 0
        }
    
    data = response.json()
    confidence = 30 if username.lower() in data.get("login", "").lower() else 0
    confidence += 20 if similar(username, data.get("name", "")) > 0.6 else 0
    confidence += 20 if data.get("followers", 0) > 5 else 0
    bio_text = data.get("bio", "")
    links = extract_links(bio_text) + ([data.get("blog")] if data.get("blog") else [])

    return {
        "Platform": "GitHub",
        "Username": username,
        "Full Name": data.get("name", "N/A"),
        "Bio": bio_text,
        "Followers": data.get("followers", 0),
        "Following": data.get("following", 0),
        "Profile URL": data.get("html_url", "N/A"),
        "Blog/Links": links,
        "Company": data.get("company", "N/A"),
        "Location": data.get("location", "N/A"),
        "Public Repos": data.get("public_repos", 0),
        "Created At": data.get("created_at", "N/A"),
        "Twitter": f"https://twitter.com/{data.get('twitter_username')}" if data.get("twitter_username") else "N/A",
        "Confidence Score": confidence
    }

def get_steam_profile(username):
    url = f"https://steamcommunity.com/id/{username}"
    response = requests.get(url)
    
    if response.status_code != 200 or "The specified profile could not be found" in response.text:
        return {
            "Platform": "Steam",
            "Username": username,
            "Full Name": colored("Profile not found", "red"),
            "Profile URL": colored("Profile not found", "red"),
            "External Links": colored("Profile not found", "red"),
            "Avatar URL": colored("Profile not found", "red"),
            "Location": colored("Profile not found", "red"),
            "Bio": colored("Profile not found", "red")
        }
    
    soup = BeautifulSoup(response.text, "html.parser")
    name_tag = soup.find("span", class_="actual_persona_name")
    full_name = name_tag.text.strip() if name_tag else "N/A"
    avatar_tag = soup.find("div", class_="playerAvatarAutoSizeInner").find("img")
    avatar_url = avatar_tag["src"] if avatar_tag else "N/A"
    location_tag = soup.find("div", class_="profile_flag")
    location = location_tag.text.strip() if location_tag else "N/A"
    bio_tag = soup.find("div", class_="profile_summary")
    bio = bio_tag.text.strip() if bio_tag else "N/A"
    
    return {
        "Platform": "Steam",
        "Username": username,
        "Full Name": full_name,
        "Profile URL": url,
        "External Links": extract_links(soup.text),
        "Avatar URL": avatar_url,
        "Location": location,
        "Bio": bio
    }

def get_roblox_profile(username):
    url = f"https://www.roblox.com/users/profile?username={username}"
    response = requests.get(url)
    
    if response.status_code != 200 or "Page cannot be found" in response.text:
        return {
            "Platform": "Roblox",
            "Username": username,
            "Full Name": colored("Profile not found", "red"),
            "Profile URL": colored("Profile not found", "red"),
            "External Links": colored("Profile not found", "red"),
            "Avatar URL": colored("Profile not found", "red"),
            "Location": colored("Profile not found", "red"),
            "Bio": colored("Profile not found", "red")
        }
    
    soup = BeautifulSoup(response.text, "html.parser")
    name_tag = soup.find("h1", class_="profile-name")
    full_name = name_tag.text.strip() if name_tag else "N/A"
    avatar_tag = soup.find("img", class_="avatar-card-image")
    avatar_url = avatar_tag["src"] if avatar_tag else "N/A"
    location = "N/A"  
    bio_tag = soup.find("div", class_="text-lead")
    bio = bio_tag.text.strip() if bio_tag else "N/A"
    
    return {
        "Platform": "Roblox",
        "Username": username,
        "Full Name": full_name,
        "Profile URL": url,
        "External Links": extract_links(soup.text),
        "Avatar URL": avatar_url,
        "Location": location,
        "Bio": bio
    }
def get_strava_profile(username):
    url = f"https://www.strava.com/athletes/{username}"
    response = requests.get(url)
    
    if response.status_code != 200 or "Page not found" in response.text:
        return {
            "Platform": "Strava",
            "Username": username,
            "Full Name": colored("Profile not found", "red"),
            "Profile URL": colored("Profile not found", "red"),
            "External Links": colored("Profile not found", "red"),
            "Avatar URL": colored("Profile not found", "red"),
            "Location": colored("Profile not found", "red"),
            "Bio": colored("Profile not found", "red")
        }
    
    soup = BeautifulSoup(response.text, "html.parser")
    name_tag = soup.find("title")
    full_name = name_tag.text.strip() if name_tag else "N/A"
    avatar_tag = soup.find("img", class_="athlete-avatar")
    avatar_url = avatar_tag["src"] if avatar_tag else "N/A"
    bio = "N/A" 
    
    return {
        "Platform": "Strava",
        "Username": username,
        "Full Name": full_name,
        "Profile URL": url,
        "External Links": extract_links(soup.text),
        "Avatar URL": avatar_url,
        "Location": "N/A",
        "Bio": bio
    }

def get_amazon_profile(username):
    url = f"https://www.amazon.com/gp/profile/{username}"
    response = requests.get(url)
    
    if response.status_code != 200 or "Sorry! We couldn't find that page" in response.text:
        return {
            "Platform": "Amazon",
            "Username": username,
            "Full Name": colored("Profile not found", "red"),
            "Profile URL": colored("Profile not found", "red"),
            "External Links": colored("Profile not found", "red"),
            "Avatar URL": colored("Profile not found", "red"),
            "Location": colored("Profile not found", "red"),
            "Bio": colored("Profile not found", "red")
        }
    
    soup = BeautifulSoup(response.text, "html.parser")
    name_tag = soup.find("span", class_="a-profile-name")
    full_name = name_tag.text.strip() if name_tag else "N/A"
    avatar_tag = soup.find("img", class_="a-profile-avatar")
    avatar_url = avatar_tag["src"] if avatar_tag else "N/A"
    bio = "N/A" 
    
    return {
        "Platform": "Amazon",
        "Username": username,
        "Full Name": full_name,
        "Profile URL": url,
        "External Links": extract_links(soup.text),
        "Avatar URL": avatar_url,
        "Location": "N/A",
        "Bio": bio
    }
def get_soundcloud_profile(username):
    url = f"https://soundcloud.com/{username}"
    response = requests.get(url)
    
    if response.status_code != 200 or "We can’t find that user" in response.text:
        return {
            "Platform": "SoundCloud",
            "Username": username,
            "Full Name": colored("Profile not found", "red"),
            "Profile URL": colored("Profile not found", "red"),
            "External Links": colored("Profile not found", "red"),
            "Avatar URL": colored("Profile not found", "red"),
            "Location": colored("Profile not found", "red"),
            "Bio": colored("Profile not found", "red")
        }
    
    soup = BeautifulSoup(response.text, "html.parser")
    name_tag = soup.find("meta", attrs={"property": "og:title"})
    full_name = name_tag["content"] if name_tag else "N/A"
    avatar_tag = soup.find("meta", attrs={"property": "og:image"})
    avatar_url = avatar_tag["content"] if avatar_tag else "N/A"
    bio_tag = soup.find("meta", attrs={"property": "og:description"})
    bio = bio_tag["content"] if bio_tag else "N/A"
    
    return {
        "Platform": "SoundCloud",
        "Username": username,
        "Full Name": full_name,
        "Profile URL": url,
        "External Links": extract_links(soup.text),
        "Avatar URL": avatar_url,
        "Location": "N/A",
        "Bio": bio
    }

def get_spotify_profile(username):
    url = f"https://open.spotify.com/user/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200 or "This page does not exist" in response.text:
        return {
            "Platform": "Spotify",
            "Username": username,
            "Full Name": colored("NOT FIXED", "blue"),
            "Profile URL": colored("NOT FIXED", "blue"),
            "External Links": colored("NOT FIXED", "blue"),
            "Avatar URL": colored("NOT FIXED", "blue"),
            "Location": colored("NOT FIXED", "blue"),
            "Bio": colored("NOT FIXED", "blue")
        }
    
    soup = BeautifulSoup(response.text, "html.parser")
    name_tag = soup.find("meta", attrs={"property": "og:title"})
    full_name = name_tag["content"] if name_tag else "N/A"
    avatar_tag = soup.find("meta", attrs={"property": "og:image"})
    avatar_url = avatar_tag["content"] if avatar_tag else "N/A"
    bio_tag = soup.find("meta", attrs={"property": "og:description"})
    bio = bio_tag["content"] if bio_tag else "N/A"
    
    return {
        "Platform": "Spotify",
        "Username": username,
        "Full Name": full_name,
        "Profile URL": url,
        "External Links": extract_links(soup.text),
        "Avatar URL": avatar_url,
        "Location": "N/A",
        "Bio": bio
    }
def get_pinterest_profile(username):
    url = f"https://www.pinterest.com/{username}/"
    response = requests.get(url)
    
    if response.status_code != 200 or "Page not found" in response.text:
        return {
            "Platform": "Pinterest",
            "Username": username,
            "Full Name": colored("Profile not found", "red"),
            "Profile URL": colored("Profile not found", "red"),
            "External Links": colored("Profile not found", "red"),
            "Avatar URL": colored("Profile not found", "red"),
            "Location": colored("Profile not found", "red"),
            "Bio": colored("Profile not found", "red")
        }
    
    soup = BeautifulSoup(response.text, "html.parser")
    name_tag = soup.find("meta", attrs={"property": "og:title"})
    full_name = name_tag["content"] if name_tag else "N/A"
    avatar_tag = soup.find("meta", attrs={"property": "og:image"})
    avatar_url = avatar_tag["content"] if avatar_tag else "N/A"
    bio_tag = soup.find("meta", attrs={"property": "og:description"})
    bio = bio_tag["content"] if bio_tag else "N/A"
    
    return {
        "Platform": "Pinterest",
        "Username": username,
        "Full Name": full_name,
        "Profile URL": url,
        "External Links": extract_links(soup.text),
        "Avatar URL": avatar_url,
        "Location": "N/A",
        "Bio": bio
    }


def check_username_on_platforms(username):
    platforms = {
        "Instagram": get_instagram_profile,
        "Twitter": get_twitter_profile,
        "GitHub": get_github_profile,
        "Steam": get_steam_profile,
        "Roblox": get_roblox_profile,
        "Strava": get_strava_profile,
        "Amazon": get_amazon_profile,
        "SoundCloud": get_soundcloud_profile,
        "Spotify": get_spotify_profile,
        "Pinterest": get_pinterest_profile
    }
    
    results = []
    for platform, func in platforms.items():
        try:
            profile = func(username)
            results.append(profile)
        except Exception as e:
            results.append({"Platform": platform, "Username": username, "Error": colored(str(e), "red")})
    
    return results

if __name__ == "__main__":
    print(ascii_art)
    username = input(" Enter the username to search: ")
    print('if the instagram profile is public the post will be shown')
    print('for BTC donations:bc1qje465lpcs06ccmywj4fer76zhpz8rgav905jsg  ')
    platforms = [check_username_on_platforms]
    results = []
    
    print("\nSearching, please wait...\n")
    for platform in tqdm(platforms, desc=" Progression"):
        result = platform(username)
        results.extend(result)
        time.sleep(0.5)  
    
    print("\nSearch Results:")
    for result in results:
        print("\n-----------------------------------")
        for key, value in result.items():
            if key == "Recent Posts" and isinstance(value, list):
                print(f"➡️ {key}:")
                for post in value:
                    print(f"    {post}")
                show_instagram_images(value) 
            else:
                print(f"➡️ {key}: {value}")