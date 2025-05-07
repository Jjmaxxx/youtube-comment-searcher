from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import csv
import re

load_dotenv() 

API_KEY = os.getenv("GOOGLE_API_KEY")
VIDEO_ID = 'ImuWa3SJulY'
SEARCH_TERMS = [s.lower() for s in [
    "jpop", "anime", "sounds like" 
]]


def contains_korean(text):
    return bool(re.search('[\uac00-\ud7af\u1100-\u11ff]', text))

translate = build('translate', 'v2', developerKey=API_KEY)
def translate_text(text, target_language='en', source_language = 'ko'):
    result = translate.translations().list(
        source=source_language, 
        target=target_language,
        q=[text]
    ).execute()
    return result['translations'][0]['translatedText']

youtube = build('youtube', 'v3', developerKey=API_KEY, static_discovery=False)

def match(text, terms):
    text = text.lower()
    return any(term in text for term in terms)

def get_matching_comments(video_id, search_terms):
    results = []
    request = youtube.commentThreads().list(
        part="snippet,replies",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request:
        response = request.execute()
        for item in response.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]["snippet"]
            top_text = top_comment["textDisplay"]
            if match(top_text, search_terms):
                if contains_korean(top_text):
                    top_text = translate_text(top_text)
                results.append({
                    "type": "top-level",
                    "author": top_comment["authorDisplayName"],
                    "text": top_text
                })

            if "replies" in item:
                for reply in item["replies"]["comments"]:
                    reply_snippet = reply["snippet"]
                    reply_text = reply_snippet["textDisplay"]
                    if contains_korean(reply_text):
                        reply_text = translate_text(reply_text)
                    results.append({
                        "type": "reply",
                        "author": reply_snippet["authorDisplayName"],
                        "text": reply_text
                    })

        request = youtube.commentThreads().list_next(request, response)

    return results

def save_to_csv(matches, filename="matching_comments.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["type", "author", "text"])
        writer.writeheader()
        for row in matches:
            writer.writerow(row)

matches = get_matching_comments(VIDEO_ID, SEARCH_TERMS)
save_to_csv(matches)

print(f"Exported {len(matches)} matching comments to matching_comments.csv")