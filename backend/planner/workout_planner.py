# backend/planner/workout_planner.py

import os
import asyncio
from groq import Groq


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable is not set")

client = Groq(api_key=GROQ_API_KEY)


def _build_workout_prompt(profile: dict) -> str:
    name = profile.get("name", "the user")
    age = profile.get("age")
    gender = profile.get("gender")
    height = profile.get("height_cm")
    weight = profile.get("weight_kg")
    goal = profile.get("primary_goal")
    activity = profile.get("activity_level")
    constraints = profile.get("constraints") or "None specified"
    diet_type = profile.get("diet_type")

    goal_map = {
        "fat_loss": "fat loss",
        "muscle_gain": "muscle gain",
        "recomposition": "body recomposition",
        "maintenance": "maintenance",
    }
    activity_map = {
        "sedentary": "sedentary",
        "light": "lightly active",
        "moderate": "moderately active",
        "high": "very active",
    }

    return f"""
You are an experienced strength & conditioning coach.

Design a **gym + home friendly workout plan** in Markdown for {name}.

User profile:
- Age: {age}
- Gender: {gender}
- Height: {height} cm
- Weight: {weight} kg
- Primary goal: {goal_map.get(goal, goal)}
- Activity level: {activity_map.get(activity, activity)}
- Diet type: {diet_type}
- Constraints / preferences: {constraints}

Assume access to: dumbbells, barbells, bench, cable machine, and some days at home with only bodyweight.

Requirements:
- Format as **4–6 week progression**, but keep it readable on one screen.
- Propose a **weekly split** (e.g., Push/Pull/Legs + optional full-body).
- For each training day, list:
  - Warm-up (3–5 minutes, very short bullets).
  - 5–7 main exercises with:
    - Sets x reps
    - RPE or difficulty cue like “easy / medium / hard”.
  - Quick **form notes** focusing on common mistakes (knees, spine, shoulders).
- Make it **PCOS-friendly**:
  - Emphasize progressive strength training and walking.
  - Avoid very extreme HIIT volume.
- Add a small section:
  - “If you only have 30 minutes” – a cut-down version.
  - “If you feel low on energy / period day” – gentler alternative.

Output: pure Markdown, clean headings, no extra explanation outside the plan.
    """.strip()


def _call_groq_workout(profile: dict) -> str:
    prompt = _build_workout_prompt(profile)

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful, realistic strength coach.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
        max_tokens=1800,
    )

    return resp.choices[0].message.content.strip()


class WorkoutPlanner:
    @staticmethod
    async def generate_workout(profile: dict) -> str:
        return await asyncio.to_thread(_call_groq_workout, profile)
