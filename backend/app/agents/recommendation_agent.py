"""
Personalized Recommendation Agent — generates tailored care advice.
Uses pet profile + behavior history to produce diet/exercise/enrichment recommendations.
"""

import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base import BaseAgent
from app.models.pet import Pet
from app.models.behavior_log import BehaviorLog
from app.models.recommendation import Recommendation
from app.core.config import settings

logger = logging.getLogger(__name__)


class RecommendationAgent(BaseAgent):
    name = "recommendation_agent"
    description = "Generates personalized care recommendations based on pet data"

    async def run(
        self,
        message: str,
        user_id: str,
        pet_id: Optional[str],
        db: AsyncSession,
        **kwargs: Any,
    ) -> str:
        if not pet_id:
            return "Please select a pet to get personalized recommendations."

        # Gather pet profile
        result = await db.execute(select(Pet).where(Pet.id == pet_id))
        pet = result.scalar_one_or_none()
        if not pet:
            return "Pet not found."

        # Gather recent behavior logs
        result = await db.execute(
            select(BehaviorLog)
            .where(BehaviorLog.pet_id == pet_id)
            .order_by(BehaviorLog.logged_at.desc())
            .limit(20)
        )
        logs = list(result.scalars().all())

        if settings.GEMINI_API_KEY:
            try:
                response = await self._call_gemini(pet, logs)
            except Exception as e:
                logger.error(f"Recommendation agent Gemini error: {e}")
                if settings.ANTHROPIC_API_KEY:
                    try:
                        response = await self._call_claude(pet, logs)
                    except Exception as ce:
                        logger.error(f"Recommendation agent Claude error: {ce}")
                        response = self._mock_recommendations(pet, logs)
                else:
                    response = self._mock_recommendations(pet, logs)
        elif settings.ANTHROPIC_API_KEY:
            try:
                response = await self._call_claude(pet, logs)
            except Exception as e:
                logger.error(f"Recommendation agent Claude error: {e}")
                response = self._mock_recommendations(pet, logs)
        else:
            response = self._mock_recommendations(pet, logs)


        # Persist the recommendation
        rec = Recommendation(
            pet_id=pet_id,
            agent_source=self.name,
            content=response,
        )
        db.add(rec)
        await db.flush()

        return response

    async def _call_gemini(self, pet: Pet, logs: list[BehaviorLog]) -> str:
        """Generate recommendations using Google Gemini API."""
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        logs_summary = "\n".join([
            f"- {log.logged_at.strftime('%Y-%m-%d')}: {log.category} = {log.value or 'N/A'}"
            for log in logs[:10]
        ])

        prompt = (
            f"You are Haven Pet AI, an expert veterinary consultant and pet care specialist.\n"
            f"Based on the following pet profile and recent behavior data, provide comprehensive, "
            f"highly detailed personalized care recommendations tailored specifically to their species ({pet.species}) "
            f"and breed ({pet.breed or 'General'}).\n\n"
            f"Pet Profile:\n"
            f"- Name: {pet.name}\n"
            f"- Species: {pet.species}\n"
            f"- Breed: {pet.breed or 'unknown'}\n"
            f"- DOB: {pet.dob or 'unknown'}\n"
            f"- Weight: {pet.weight or 'unknown'} kg\n"
            f"- Gender: {pet.gender or 'unknown'}\n\n"
            f"Recent Behavior Logs:\n{logs_summary or 'No recent logs recorded'}\n\n"
            f"Provide actionable, expert care recommendations for:\n"
            f"1. 🍽️ Diet & Nutrition\n"
            f"2. 🏠 Habitat & Living Environment\n"
            f"3. 🏃 Physical Exercise & Daily Activity\n"
            f"4. 🧠 Mental Enrichment & Behavioral Training\n"
            f"5. 🏥 Health & Species-Specific Preventative Care\n\n"
            f"Format cleanly using markdown and bullet points with emoji headers."
        )

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text.strip()
        except Exception as err:
            logger.warning(f"gemini-2.5-flash failed ({err}), retrying with gemini-1.5-flash...")
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
            )
            return response.text.strip()

    async def _call_claude(self, pet: Pet, logs: list[BehaviorLog]) -> str:
        """Generate recommendations using Claude."""

        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        logs_summary = "\n".join([
            f"- {log.logged_at.strftime('%Y-%m-%d')}: {log.category} = {log.value or 'N/A'}"
            for log in logs[:10]
        ])

        prompt = (
            f"Based on the following pet profile and recent behavior data, provide highly detailed "
            f"personalized care recommendations tailored specifically to their species ({pet.species}) "
            f"and breed ({pet.breed or 'General'}).\n\n"
            f"Pet: {pet.name}, Species: {pet.species}, Breed: {pet.breed or 'unknown'}, "
            f"DOB: {pet.dob or 'unknown'}, Weight: {pet.weight or 'unknown'} kg, "
            f"Gender: {pet.gender or 'unknown'}\n\n"
            f"Recent Behavior Logs:\n{logs_summary or 'No recent logs'}\n\n"
            f"Provide actionable, expert recommendations for:\n"
            f"1. 🍽️ Diet & Nutrition\n"
            f"2. 🏠 Habitat & Environment (lighting, temp, space)\n"
            f"3. 🏃 Physical Exercise & Out-of-cage / Play routine\n"
            f"4. 🧠 Mental Enrichment & Behavioral Training\n"
            f"5. 🏥 Health & Species-Specific Care Guidelines\n\n"
            f"Format cleanly with emoji headers."
        )

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def _mock_recommendations(self, pet: Pet, logs: list[BehaviorLog]) -> str:
        """Generate comprehensive species and breed specific care advice."""
        species = (pet.species or "pet").lower()
        breed = (pet.breed or "").strip()
        name = pet.name

        if "dog" in species:
            breed_str = f" ({breed})" if breed else ""
            weight_str = f"At {pet.weight} kg, maintain balanced caloric intake." if pet.weight else "Monitor weight monthly."
            return (
                f"# 🐕 Tailored Care Guide for {name}{breed_str}\n\n"
                f"## 🍽️ Diet & Nutrition\n"
                f"• Feed high-quality protein-first food matched to size & life stage.\n"
                f"• {weight_str}\n"
                f"• Omega-3 fatty acids (fish oil) support joint mobility and coat shine.\n\n"
                f"## 🏠 Living Space & Rest\n"
                f"• Provide an orthopedic bed away from cold drafts.\n"
                f"• Establish a consistent sleep schedule of 12-14 hours per day.\n\n"
                f"## 🏃 Daily Exercise\n"
                f"• Minimum 45-60 minutes of daily physical exercise (walks, agility, fetch).\n"
                f"• Breed note for {breed or 'active dogs'}: engage in stamina-building activities.\n\n"
                f"## 🧠 Mental Enrichment\n"
                f"• Use puzzle feeders, scent-work games, and positive reinforcement training.\n"
                f"• Rotate toys weekly to prevent boredom.\n\n"
                f"## 🏥 Health & Grooming\n"
                f"• Brush teeth 3x weekly and clip nails every 3-4 weeks.\n"
                f"• Maintain annual core vaccinations and parasite preventative treatment."
            )
        elif "cat" in species:
            breed_str = f" ({breed})" if breed else ""
            return (
                f"# 🐱 Tailored Care Guide for {name}{breed_str}\n\n"
                f"## 🍽️ Diet & Nutrition\n"
                f"• Cats are obligate carnivores: provide meat-based wet food for optimal hydration.\n"
                f"• Feed measured portions twice daily; limit high-calorie treats.\n\n"
                f"## 🏠 Habitat & Environment\n"
                f"• Provide vertical space (cat trees, window perches) for security and exercise.\n"
                f"• Maintain clean litter boxes (1 per cat + 1 extra), scooped daily.\n\n"
                f"## 🏃 Play & Exercise\n"
                f"• Engage in 2-3 interactive play sessions daily (15 mins each) using wand toys.\n"
                f"• Stimulate the natural 'hunt-eat-groom-sleep' cycle.\n\n"
                f"## 🧠 Mental Enrichment\n"
                f"• Window perches for bird watching, cat grass, and treat puzzle balls.\n\n"
                f"## 🏥 Health & Grooming\n"
                f"• Daily brushing for medium/long hair breeds to prevent hairballs.\n"
                f"• Monitor hydration and urinary tract health regularly."
            )
        elif "bird" in species or "parrot" in species or "cockatiel" in species:
            breed_str = f" ({breed})" if breed else ""
            return (
                f"# 🦜 Tailored Care Guide for {name}{breed_str}\n\n"
                f"## 🍽️ Diet & Nutrition\n"
                f"• Base diet: 60-70% high-quality formulated pellets, 20-30% fresh veggies (leafy greens, carrots, broccoli), and limited seeds as treats.\n"
                f"• Avoid avocado, chocolate, caffeine, onions, and fruit pits (toxic to birds).\n\n"
                f"## 🏠 Cage & Environmental Needs\n"
                f"• Large cage allowing full wing expansion with varied natural wood perches.\n"
                f"• Strict safety warning: Never use non-stick (Teflon/PTFE) cookware, scented candles, or aerosols near birds.\n\n"
                f"## 🏃 Flight & Exercise\n"
                f"• 2-4 hours of supervised out-of-cage flight and perching time daily in a bird-proof room.\n\n"
                f"## 🧠 Foraging & Mental Stimulation\n"
                f"• Provide shreddable paper toys, wooden blocks, and foraging boxes to satisfy chewing instincts.\n"
                f"• Target training and trick training foster strong social bonds.\n\n"
                f"## 🏥 Health & Respiratory Care\n"
                f"• Provide shallow misting or water dish baths 2-3 times per week for feather maintenance.\n"
                f"• Schedule annual checkups with a specialized avian veterinarian."
            )
        elif "lizard" in species or "reptile" in species or "gecko" in species or "snake" in species:
            breed_str = f" ({breed})" if breed else ""
            return (
                f"# 🦎 Tailored Care Guide for {name}{breed_str}\n\n"
                f"## 🍽️ Diet & Nutrition\n"
                f"• Provide species-appropriate insects (crickets, dubia roaches), leafy greens (collard, dandelion greens), or clean prey.\n"
                f"• Dust food with Calcium + D3 supplement 3x weekly and multivitamin weekly.\n\n"
                f"## 🏠 Terrarium & Thermal Gradients\n"
                f"• Maintain a strict thermal gradient (basking spot 95-105°F / cool side 75-80°F).\n"
                f"• Provide essential 10.0 T5 High-Output UVB lighting replaced every 6-12 months.\n"
                f"• Monitor humidity levels using digital hygrometers.\n\n"
                f"## 🏃 Physical Activity & Handling\n"
                f"• Provide climbing branches, rocks, and secure hideouts on both warm and cool sides.\n"
                f"• Gentle, regular handling outside the terrarium once pet is acclimated.\n\n"
                f"## 🧠 Habitat Enrichment\n"
                f"• Add bio-active substrates, slate rocks, and climbing hammocks.\n\n"
                f"## 🏥 Shedding & Reptile Wellness\n"
                f"• Provide a humid hide box to assist clean, complete skin shedding.\n"
                f"• Consult a specialized reptile vet for stool checks and health monitoring."
            )
        elif "rabbit" in species or "bunny" in species:
            breed_str = f" ({breed})" if breed else ""
            return (
                f"# 🐇 Tailored Care Guide for {name}{breed_str}\n\n"
                f"## 🍽️ Diet & Nutrition\n"
                f"• Unlimited fresh Timothy Hay (80% of total diet) to maintain GI tract motility and wear down teeth.\n"
                f"• Fresh leafy greens (romaine, parsley, cilantro) daily and a small portion of high-fiber pellets.\n"
                f"• Fresh water in a heavy ceramic bowl or gravity feeder at all times.\n\n"
                f"## 🏠 Housing & Bunny-Proofing\n"
                f"• Provide an exercise pen or free-roam space; cages must allow 4+ full hops.\n"
                f"• Bunny-proof all electrical wires, baseboards, and houseplants.\n\n"
                f"## 🏃 Physical Activity\n"
                f"• Minimum 3-4 hours of daily out-of-pen roaming and exercise during twilight hours.\n\n"
                f"## 🧠 Mental Enrichment\n"
                f"• Tunnel tubes, cardboard dig boxes filled with hay, and chewable applewood sticks.\n\n"
                f"## 🏥 Health & GI Stasis Prevention\n"
                f"• Monitor daily poop size and appetite — immediate vet visit if rabbit stops eating for >12 hrs (GI stasis emergency).\n"
                f"• Brush regularly during shedding seasons to prevent hair ingestion."
            )
        elif "insect" in species or "tarantula" in species or "mantis" in species or "beetle" in species:
            breed_str = f" ({breed})" if breed else ""
            return (
                f"# 🦗 Tailored Care Guide for {name}{breed_str}\n\n"
                f"## 🍽️ Diet & Feeding Schedule\n"
                f"• Feed gut-loaded live crickets, mealworms, or fruit flies every 3-7 days based on size and species.\n"
                f"• Remove uneaten live prey after 12 hours to prevent prey from harming a resting or moulting insect.\n\n"
                f"## 🏠 Enclosure & Moisture Control\n"
                f"• Maintain species-appropriate moisture and substrate dampness (coco fiber, peat moss).\n"
                f"• Ensure cross-ventilation to prevent mold growth while maintaining humidity.\n\n"
                f"## 🏃 Physical Setup & Climbing\n"
                f"• For arboreal species: provide vertical cork bark and fake foliage.\n"
                f"• For terrestrial species: ensure shallow substrate depth to prevent falls.\n\n"
                f"## 🧠 Behavioral Care\n"
                f"• Minimize unnecessary handling to reduce stress on fragile exoskeletons.\n\n"
                f"## 🏥 Moulting Safety & Care\n"
                f"• Never disturb or touch an insect/tarantula while in premoult or moulting.\n"
                f"• Keep water dishes shallow with pebbles to prevent accidental drowning."
            )
        elif "fish" in species or "aquatic" in species:
            breed_str = f" ({breed})" if breed else ""
            return (
                f"# 🐠 Tailored Care Guide for {name}{breed_str}\n\n"
                f"## 🍽️ Diet & Feeding\n"
                f"• Feed high-grade aquatic pellets or frozen daphnia/bloodworms twice daily.\n"
                f"• Never overfeed — only what can be consumed within 2 minutes.\n\n"
                f"## 🏠 Tank Parameters & Environment\n"
                f"• Maintain stable water temperature (75-80°F for tropical fish) with reliable heater.\n"
                f"• Perform 20-25% weekly water changes using dechlorinated water.\n\n"
                f"## 🧠 Aquascaping Enrichment\n"
                f"• Provide live plants (Anubias, Java Fern) and smooth cave shelters.\n\n"
                f"## 🏥 Water Chemistry & Health\n"
                f"• Test Ammonia, Nitrite (0 ppm), and Nitrate (<20 ppm) weekly using liquid test kits."
            )
        else:
            breed_str = f" ({breed})" if breed else ""
            return (
                f"# 🐾 Tailored Care Guide for {name} ({species}){breed_str}\n\n"
                f"## 🍽️ Diet & Nutrition\n"
                f"• Provide species-appropriate balanced diet and fresh water daily.\n"
                f"• Consult specialized care guides or an exotic veterinarian for exact caloric needs.\n\n"
                f"## 🏠 Environment & Habitat\n"
                f"• Maintain optimal temperature, humidity, and shelter tailored to species requirements.\n\n"
                f"## 🏃 Activity & Enrichment\n"
                f"• Provide daily out-of-cage time, interactive toys, and foraging activities.\n\n"
                f"## 🏥 Preventative Health\n"
                f"• Keep detailed health records and schedule routine veterinary wellness exams."
            )

