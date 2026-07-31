import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Tennis Footwork Drills for Faster Movement",
        "5 Exercises to Strengthen Your Tennis Game",
        "The Athlete's Guide to Smart Recovery",
        "Pre-Match Nutrition That Fuels Performance",
        "Train Like a Tennis Pro: Daily Routine",
        "Why Consistency Beats Intensity in Training",
        "Wellness Habits of Top Athletes",
        "Recovery Day Essentials for Players",
        "Travel Fitness: Stay Active on the Road",
        "Tennis Training You Can Do at Home",
        "The Mental Side of Winning Matches",
        "Healthy Living for Peak Performance",
        "Your Daily Dose of Athletic Motivation",
        "Core Strength for Powerful Serves",
        "Warm-Up Routine Before Every Match",
    ]

    fallback_descriptions = [
        "Footwork is everything in tennis — the game is won in the first three steps. Quick, light footwork keeps you balanced and ready for every shot. Add these drills to your training and watch your movement transform. Comment your favorite drill below! 🎾 #tennis #tennistraining #footwork #athlete #trainingdrills #amelienorthcott",
        "Strength training off the court makes you stronger on it. Core, legs, and shoulders form the foundation of a powerful serve and explosive movement. You don't need a gym — bodyweight work goes a long way. Save this for your next workout! 💪 #tennisfitness #strengthtraining #workout #corestrength #tennisathlete #amelienorthcott",
        "Recovery isn't laziness — it's part of training. Sleep, stretching, hydration, and proper nutrition are how your body rebuilds stronger. Athletes who recover well, perform well. Drop a 🌿 if you're prioritizing recovery this week! #recovery #restday #wellness #athlete #performance #amelienorthcott",
        "What you eat before a match matters. Fuel with complex carbs, hydrate properly, and time your meals so energy peaks when you step on court. Your performance starts at the table. Like if you're taking nutrition seriously! 🥗 #sportsnutrition #tennisdiet #prematch #fueling #healthyathlete #amelienorthcott",
        "Consistency beats intensity every time. Showing up daily — even for 30 focused minutes — creates results that crash-course training never will. Build the habit, and the improvement follows. Double tap if you train consistently! 🏆 #consistency #trainingroutine #tennislife #discipline #improvement #amelienorthcott",
        "The mental game is half the match. Breathing, focus, and staying present under pressure separate good players from great ones. Train your mind like you train your body. Share this with a player who needs it! 🧠 #tennismindset #mentalgame #focus #sportspsychology #winning #amelienorthcott",
        "Wellness is the foundation of an athletic life — sleep, stress management, and time outside keep you healthy and performing. You can't out-train poor habits. Take care of the whole athlete, not just the muscles. Comment how you recharge! 🌸 #wellness #healthyliving #athleticlifestyle #balance #selfcare #amelienorthcott",
        "Traveling doesn't mean losing your fitness. Bodyweight circuits, hotel workouts, and smart eating keep you on track anywhere. Stay active, stay sharp, and enjoy the journey. Save this for your next trip! ✈️ #travelfitness #hotelworkout #activeifestyle #fitontheroad #tennistravel #amelienorthcott",
        "You can train tennis at home — shadow swings, wall drills, and footwork patterns build skills between court sessions. Consistency at home compounds into confidence on court. Share this with your training partner! 🎾 #homeworkout #tennisdrills #trainingtips #athlete #dailyroutine #amelienorthcott",
        "Motivation gets you started; discipline keeps you going. On the days you don't feel like training, show up anyway — those are the days that build champions. Future you is watching. Drop a 🔥 if you showed up today! #discipline #motivation #athletemindset #tennislife #nevergiveup #amelienorthcott",
        "Core strength powers every part of your game — serves, groundstrokes, and quick changes of direction. A strong core protects you and adds power to your shots. Add these moves to your routine. Like if you're building your core! 🏋️ #coretraining #tennisfitness #strength #sportsperformance #tennisworkout #amelienorthcott",
        "A proper warm-up protects you and primes your body to perform. Light cardio, dynamic stretching, and a few practice swings get you ready to compete from the first point. Never skip it. Save this as your pre-match checklist! ✅ #warmup #prematchroutine #injuryprevention #tennisready #athlete #amelienorthcott",
        "Healthy living isn't just training — it's how you eat, sleep, and move through your day. Small daily choices build a strong, resilient body that loves the game. Start with one good habit today. Comment one you're adding! 🌱 #healthyliving #habits #athleticlife #wellness #tennisfit #amelienorthcott",
        "Daily inspiration from the court: every match, win or lose, teaches you something. The lessons — resilience, focus, growth — carry far beyond tennis. Keep playing, keep learning, keep growing. Drop a 🎾 if you love this game! #tennislife #inspiration #growthmindset #sportsvalues #loveofthegame #amelienorthcott",
        "End strong, recover harder. Post-training stretching, protein, and rest are how champions stay consistent. Honor your body and it will carry you through every match and every season. Good night, athletes. 🌙 #postworkout #recovery #athleteroutine #selfcare #tennisplayer #amelienorthcott",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "energetic and athletic — make viewers want to hit the court now",
        "coach-like and practical — give honest training and nutrition advice",
        "motivating and competitive — inspire discipline and peak performance",
        "wellness-focused — emphasise recovery, healthy living and balance",
        "personal and inspiring — share real athlete experiences and lessons",
        "smart and performance-driven — explain the why behind the training",
        "warm and encouraging — celebrate progress and love of the game",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Amelie Northcott'. "
        f"The page covers tennis training, fitness and workouts, healthy living, wellness and recovery, travel and lifestyle, and daily inspiration. It's athletic, energetic, and speaks to people who love tennis and want to stay fit and healthy while living an active lifestyle. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if this motivated your training! Comment your fitness goal below! Share this with a tennis friend! Follow Amelie Northcott for daily fitness and tennis inspiration!"
        f"Include relevant hashtags in ALL LOWERCASE such as #tennis #tennistraining #fitness #workout #healthyliving #wellness #recovery #athlete #sports #tennislife #matchday #active #motivation #amelienorthcott. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["tennis", "tennistraining", "fitness", "workout", "healthyliving", "wellness", "recovery", "athlete", "sports", "tennislife", "matchday", "active", "motivation", "amelienorthcott"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
