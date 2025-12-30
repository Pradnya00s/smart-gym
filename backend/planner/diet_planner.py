# backend/planner/diet_planner.py

import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable is not set")

client = Groq(api_key=GROQ_API_KEY)


class DietPlanner:
    @staticmethod
    async def generate_diet(user: dict) -> str:
        """
        Takes a user profile dict and returns a markdown/text diet plan.
        This is called by the /plan/diet endpoint.
        """

        name = user.get("name", "User")
        age = user.get("age")
        gender = user.get("gender")
        height_cm = user.get("height_cm")
        weight_kg = user.get("weight_kg")
        primary_goal = user.get("primary_goal", "fat_loss")
        activity_level = user.get("activity_level", "moderate")
        diet_type = user.get("diet_type", "mixed")
        constraints = user.get("constraints", "")

        profile_text = f"""
Name: {name}
Age: {age}
Gender: {gender}
Height: {height_cm} cm
Weight: {weight_kg} kg
Goal: {primary_goal}
Activity level: {activity_level}
Diet type: {diet_type}
Constraints / medical notes: {constraints}
"""

        system_prompt = (
            "You are a certified nutrition coach who creates practical, "
            "easy-to-follow meal plans. You specialise in Indian context, "
            "hostel/mess situations, budget friendly options, and conditions "
            "like PCOS, insulin resistance, and acne-prone skin."
        )

        user_prompt = f"""
Given this user profile:

{profile_text}

Create a 1-day sample diet plan that matches:

- The primary goal (fat loss / muscle gain / recomposition / maintenance)
- The diet type (veg / egg_veg / non_veg / vegan / mixed)
- The activity level
- Any constraints (like PCOS-friendly, avoid dairy at night, hostel mess food, etc.)

Format your answer as **clear sections** in markdown:

1. Quick summary (2–3 bullet points)
2. Suggested calories + macro split (approximate)
3. Full-day meal plan:
   - Early morning
   - Breakfast
   - Mid-morning
   - Lunch
   - Evening snack
   - Dinner
   - Optional late-night / pre-bed snack
4. Simple guidelines & habits (3–6 bullets)
5. Notes specific to Indian lifestyle (e.g. tiffin, hostel mess, street food handling)

Use simple language, no emoji, and keep it nicely formatted.
"""

        # Groq client is synchronous but we call it in an async function – fine for now.
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=1300,
        )

        text = completion.choices[0].message.content
        return text.strip() if text else "No plan generated."
