"""
Conversational AI Agent — handles free-form pet care chat.
Injects pet context into the system prompt and maintains conversation history.
Falls back to mock responses when no API key is configured.
"""

import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base import BaseAgent
from app.models.pet import Pet
from app.models.chat_message import ChatMessage, ChatRole
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConversationalAgent(BaseAgent):
    name = "conversational_agent"
    description = "Handles free-form pet care chat with context awareness"

    async def run(
        self,
        message: str,
        user_id: str,
        pet_id: Optional[str],
        db: AsyncSession,
        **kwargs: Any,
    ) -> str:
        # Check if this is a health/symptom assessment request
        is_health = kwargs.get("is_health_assessment", False)

        # Build pet context
        pet_context = ""
        if pet_id:
            result = await db.execute(select(Pet).where(Pet.id == pet_id))
            pet = result.scalar_one_or_none()
            if pet:
                pet_context = (
                    f"\nPet Profile:\n"
                    f"- Name: {pet.name}\n"
                    f"- Species: {pet.species}\n"
                    f"- Breed: {pet.breed or 'Unknown'}\n"
                    f"- DOB: {pet.dob or 'Unknown'}\n"
                    f"- Weight: {pet.weight or 'Unknown'} kg\n"
                    f"- Gender: {pet.gender or 'Unknown'}\n"
                    f"- Medical History: {pet.medical_history or 'None recorded'}\n"
                )

        # Retrieve recent conversation history (last 10 messages)
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id, ChatMessage.pet_id == pet_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
        )
        history = list(reversed(list(result.scalars().all())))

        # Try calling Gemini API
        if settings.GEMINI_API_KEY:
            try:
                return await self._call_gemini(message, pet_context, history, is_health)
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                return self._mock_response(message, pet_context, is_health)

        # Try calling Claude API
        if settings.ANTHROPIC_API_KEY:
            try:
                return await self._call_claude(message, pet_context, history, is_health)
            except Exception as e:
                logger.error(f"Claude API error: {e}")
                return self._mock_response(message, pet_context, is_health)
        else:
            return self._mock_response(message, pet_context, is_health)

    async def _call_gemini(
        self, message: str, pet_context: str, history: list[ChatMessage],
        is_health: bool = False,
    ) -> str:
        """Call Google Gemini API for pet care chat & symptom triage."""
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        system_prompt = (
            "You are Haven Pet AI, a dedicated pet care assistant assigned STRICTLY to the user's active pet profile.\n"
            "CRITICAL DIRECTIVE:\n"
            "- You MUST ONLY give answers, advice, health symptom guidance, and routines for the active pet defined in the pet profile below.\n"
            "- Do NOT give general advice for all pets or list other unrelated pet species unless the user explicitly requests a direct comparison.\n"
            "- Always address the active pet by name and adapt all recommendations specifically to its species, breed, age, and medical background.\n\n"
            "GUIDELINES:\n"
            "- Be warm, empathetic, and highly specific to this pet.\n"
            "- Use clear bullet points and emoji headers.\n"
            "- When discussing health symptoms, ask targeted follow-up questions relevant to this pet's species.\n"
            "- Always recommend consulting a certified veterinarian for serious medical concerns.\n"
            f"{pet_context}"
        )

        if is_health:
            system_prompt += (
                "\n\nIMPORTANT: The user is requesting a health/symptom assessment. "
                "Act as a pet health triage assistant. Ask targeted questions about symptoms, duration, appetite, energy levels. "
                "Provide preliminary assessment with urgency level (🟢 Mild / 🟡 Moderate / 🔴 Urgent) and recommended next steps."
            )

        full_prompt = f"{system_prompt}\n\n--- Conversation History ---\n"
        for msg in history:
            full_prompt += f"{msg.role.upper()}: {msg.content}\n"
        full_prompt += f"USER: {message}\nASSISTANT:"

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=full_prompt,
        )
        return response.text.strip()

    async def _call_claude(
        self, message: str, pet_context: str, history: list[ChatMessage],
        is_health: bool = False,
    ) -> str:
        """Call the Anthropic Claude API with conversation context."""
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        system_prompt = (
            "You are Haven Pet AI, a dedicated pet care assistant assigned STRICTLY to the user's active pet profile.\n"
            "CRITICAL DIRECTIVE:\n"
            "- You MUST ONLY give answers, advice, health symptom guidance, and routines for the active pet defined in the pet profile below.\n"
            "- Do NOT give general advice for all pets or list other unrelated pet species unless the user explicitly requests a direct comparison.\n"
            "- Always address the active pet by name and adapt all recommendations specifically to its species, breed, age, and medical background.\n\n"
            "GUIDELINES:\n"
            "- Be warm, empathetic, and highly specific to this pet.\n"
            "- Use clear bullet points and emoji headers.\n"
            "- When discussing health symptoms, ask targeted follow-up questions relevant to this pet's species.\n"
            "- Always recommend consulting a certified veterinarian for serious medical concerns.\n"
            f"{pet_context}"
        )

        if is_health:
            system_prompt += (
                "\n\nIMPORTANT: The user is requesting a health/symptom assessment. "
                "Act as a pet health triage assistant. Ask targeted questions about:\n"
                "- How long have the symptoms been present?\n"
                "- Is the pet eating/drinking normally?\n"
                "- Any changes in energy, bathroom habits, or behavior?\n"
                "- Any physical signs (swelling, discharge, rash, limping)?\n"
                "After gathering information, provide a preliminary assessment with urgency level "
                "(🟢 Mild / 🟡 Moderate / 🔴 Urgent) and recommended next steps."
            )

        messages = []
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": message})

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )

        return response.content[0].text

    def _mock_response(self, message: str, pet_context: str, is_health: bool = False) -> str:
        """Generate an intelligent multi-species response covering all pet types."""
        msg_lower = message.lower()

        # ── Symptom Checker / Health Assessment Flow ──
        if is_health or any(w in msg_lower for w in [
            "sick", "symptom", "vomit", "vomiting", "lethargy", "lethargic",
            "not eating", "won't eat", "diarrhea", "limping", "swollen", "swelling",
            "discharge", "cough", "coughing", "sneeze", "sneezing", "rash",
            "bleeding", "lump", "bump", "itching", "scratching", "losing weight",
            "breathing", "panting", "wheezing", "shaking", "trembling",
        ]):
            # Check if user has provided specific symptoms for assessment
            symptom_details = any(w in msg_lower for w in [
                "days", "hours", "week", "started", "since", "yesterday",
                "stopped eating", "won't drink", "can't walk",
            ])

            if symptom_details:
                return (
                    "🏥 **Symptom Assessment:**\n\n"
                    "Based on what you've described, here's my preliminary assessment:\n\n"
                    "**Urgency Level:** 🟡 **Moderate — Monitor Closely**\n\n"
                    "**Observations:**\n"
                    "• The symptoms you describe could indicate several conditions ranging from mild to serious.\n"
                    "• Changes in appetite, energy, or bathroom habits lasting more than 24 hours warrant veterinary attention.\n\n"
                    "**Recommended Next Steps:**\n"
                    "1. 📝 **Log everything** — Record food/water intake, bathroom output, and energy levels in the Behavior Log.\n"
                    "2. 🌡️ **Monitor temperature** — Normal ranges vary by species (Dogs: 101-102.5°F, Cats: 100.5-102.5°F).\n"
                    "3. 🏥 **Schedule a vet visit** within 24-48 hours if symptoms persist or worsen.\n\n"
                    "**⚠️ Seek immediate emergency care if you notice:**\n"
                    "• Difficulty breathing or blue/pale gums\n"
                    "• Seizures or collapse\n"
                    "• Bloated abdomen (especially in large dogs)\n"
                    "• Inability to urinate (especially in male cats)\n\n"
                    "Would you like me to help you log these symptoms in the Behavior Log for your vet visit?"
                )
            else:
                return (
                    "🩺 **Pet Health Check — Let me help assess the situation.**\n\n"
                    "To give you the best guidance, I need to ask a few questions:\n\n"
                    "**1. What symptoms are you observing?**\n"
                    "   _(e.g., vomiting, lethargy, not eating, limping, discharge, unusual behavior)_\n\n"
                    "**2. How long have the symptoms been present?**\n"
                    "   _(e.g., just started, a few hours, 1-2 days, several days)_\n\n"
                    "**3. Is your pet eating and drinking normally?**\n\n"
                    "**4. Any recent changes?**\n"
                    "   _(new food, environment change, contact with other animals, exposure to chemicals/plants)_\n\n"
                    "**Species-Specific Red Flags to Watch For:**\n"
                    "• 🐕 **Dogs:** Bloating, repeated vomiting, pale gums, difficulty breathing\n"
                    "• 🐱 **Cats:** Straining to urinate, hiding for extended periods, rapid breathing\n"
                    "• 🦜 **Birds:** Tail bobbing, sitting fluffed at bottom of cage, nasal discharge\n"
                    "• 🦎 **Reptiles:** Sunken eyes, incomplete shedding, mouth gaping\n"
                    "• 🐇 **Rabbits:** Not eating hay for >12 hours (GI stasis — emergency!)\n"
                    "• 🐠 **Fish:** Clamped fins, white spots, gasping at surface\n\n"
                    "Please describe the symptoms and I'll provide guidance! 💬"
                )

        # ── Daily Routine ──
        if any(w in msg_lower for w in ["routine", "daily", "schedule", "morning", "evening", "bedtime", "day plan"]):
            return (
                "📋 **Daily Routine Guide by Species:**\n\n"
                "**🐕 Dogs:**\n"
                "• 🌅 Morning: 15-min walk → breakfast → fresh water\n"
                "• 🌞 Midday: Mental enrichment (puzzle feeder, training session)\n"
                "• 🌆 Evening: 30-45 min exercise → dinner → bonding time\n"
                "• 🌙 Night: Final potty break → settle in designated sleep area\n\n"
                "**🐱 Cats:**\n"
                "• 🌅 Morning: Interactive play → breakfast → clean litter\n"
                "• 🌞 Midday: Window perching, cat grass, vertical exploration\n"
                "• 🌆 Evening: Wand toy session → dinner → grooming\n"
                "• 🌙 Night: Calm puzzle toy → settle (cats are crepuscular — peak activity at dawn/dusk)\n\n"
                "**🦜 Birds:**\n"
                "• 🌅 Morning: Uncover cage → fresh pellets + vegetables → misting bath\n"
                "• 🌞 Midday: 2-4 hours supervised out-of-cage time\n"
                "• 🌆 Evening: Foraging toys → social time → cover cage by sunset\n"
                "• 🌙 Night: 10-12 hours of quiet, dark sleep (essential for hormonal health)\n\n"
                "**🦎 Reptiles:**\n"
                "• 🌅 Morning: Lights on (UVB + basking) → misting → check temps\n"
                "• 🌞 Midday: Feeding (species-appropriate) → calcium dusting\n"
                "• 🌆 Evening: Handling session (if acclimated) → clean water dish\n"
                "• 🌙 Night: Lights off → nighttime temperature drop\n\n"
                "Ask about a specific species for a detailed routine! 🕐"
            )

        # ── What's Good / What's Bad ──
        if any(w in msg_lower for w in [
            "toxic", "poison", "dangerous", "safe", "can they eat",
            "good for", "bad for", "avoid", "harmful", "allowed",
        ]):
            return (
                "⚠️ **What's Safe & What's Dangerous:**\n\n"
                "**🐕 Dogs — AVOID:**\n"
                "• ❌ Chocolate, grapes, raisins, xylitol, onions, garlic, macadamia nuts\n"
                "• ❌ Cooked bones (splintering risk), avocado\n"
                "• ✅ SAFE: Carrots, blueberries, plain pumpkin, lean chicken, rice\n\n"
                "**🐱 Cats — AVOID:**\n"
                "• ❌ Onions, garlic, lilies (extremely toxic!), chocolate, caffeine, raw eggs\n"
                "• ❌ Essential oils, string/ribbon (intestinal blockage)\n"
                "• ✅ SAFE: Cooked chicken, fish, catnip, cat grass\n\n"
                "**🦜 Birds — AVOID:**\n"
                "• ❌ Avocado (lethal!), chocolate, caffeine, onions, fruit pits/seeds\n"
                "• ❌ Non-stick cookware fumes (PTFE/Teflon — instantly fatal!)\n"
                "• ❌ Scented candles, aerosol sprays, air fresheners\n"
                "• ✅ SAFE: Pellets, leafy greens, carrots, berries, squash\n\n"
                "**🦎 Reptiles — AVOID:**\n"
                "• ❌ Fireflies (toxic to lizards!), wild-caught insects, iceberg lettuce\n"
                "• ❌ Substrate that causes impaction (loose sand for young beardies)\n"
                "• ✅ SAFE: Gut-loaded crickets, dubia roaches, collard greens, butternut squash\n\n"
                "**🐇 Rabbits — AVOID:**\n"
                "• ❌ Iceberg lettuce, potatoes, bread, chocolate, yogurt drops\n"
                "• ✅ SAFE: Timothy hay (unlimited!), romaine, cilantro, parsley, apple (no seeds)\n\n"
                "Ask about a specific food or item and I'll tell you if it's safe! 🔍"
            )

        # ── Bird-specific ──
        if any(w in msg_lower for w in ["bird", "parrot", "cockatiel", "budgie", "feather", "wing", "fly"]):
            return (
                "🦜 **Avian & Bird Care Guide:**\n\n"
                "• **Nutrition:** 60-70% formulated pellets + 20-30% fresh organic vegetables (dark leafy greens, squashes). Seeds should only be occasional treats.\n"
                "• **Toxicities:** Strictly avoid avocado, chocolate, caffeine, onions, and non-stick cookware fumes (PTFE/Teflon is lethal to bird lungs!).\n"
                "• **Enrichment:** Birds are intelligent! Provide shreddable foraging toys, puzzle boxes, and 2-4 hours of daily out-of-cage supervised flight.\n"
                "• **Bath & Feather Care:** Offer daily misting or a shallow water dish to encourage natural preening."
            )

        # ── Reptile/Lizard-specific ──
        elif any(w in msg_lower for w in ["lizard", "gecko", "dragon", "reptile", "snake", "turtle", "uvb", "basking", "terrarium"]):
            return (
                "🦎 **Reptile & Lizard Care Guide:**\n\n"
                "• **Lighting & Thermal Gradients:** Require a warm basking spot (95-105°F for bearded dragons) and a cool zone (75-80°F). High-output T5 10.0 UVB lighting is non-negotiable for calcium absorption.\n"
                "• **Diet & Calcium:** Live gut-loaded crickets/dubia roaches + collard greens. Dust food with Calcium + Vitamin D3 powder 3x per week.\n"
                "• **Shedding Support:** Provide a humid hide box containing damp sphagnum moss to aid complete ecdysis (skin shedding).\n"
                "• **Hydration:** Misting and shallow water bowls help prevent impaction and kidney issues."
            )

        # ── Rabbit-specific ──
        elif any(w in msg_lower for w in ["rabbit", "bunny", "hay", "hop", "stasis"]):
            return (
                "🐇 **Rabbit & Lagomorph Care Guide:**\n\n"
                "• **Dietary Needs:** 80% of diet must be unlimited fresh Timothy Hay. Provide daily romaine/parsley and a small tablespoon of high-fiber pellets.\n"
                "• **Housing & Space:** Rabbits need x-pens or free-roam space allowing at least 4 continuous hops. Wire-bottom cages damage their hocks!\n"
                "• **GI Health Warning:** If a rabbit stops eating or pooping for >12 hours, seek immediate exotic vet emergency care for GI stasis.\n"
                "• **Bunny Proofing:** Protect all electrical cords, baseboards, and carpet corners."
            )

        # ── Insect/Arachnid-specific ──
        elif any(w in msg_lower for w in ["insect", "tarantula", "spider", "mantis", "beetle", "bug"]):
            return (
                "🦗 **Invertebrate & Insect Care Guide:**\n\n"
                "• **Enclosure Setup:** Cross-ventilation is key. Terrestrial species need shallow height to prevent fall injuries; arboreal species need vertical bark.\n"
                "• **Feeding Routine:** Offer gut-loaded crickets or mealworms every 3-7 days. Always remove uneaten prey after 12 hours!\n"
                "• **Moulting Caution:** When an insect or tarantula lies on its back to moult, DO NOT TOUCH or mist directly. They are extremely fragile until their new exoskeleton hardens."
            )

        # ── Fish/Aquatic-specific ──
        elif any(w in msg_lower for w in ["fish", "betta", "tank", "aquarium", "filter"]):
            return (
                "🐠 **Aquatic & Fish Care Guide:**\n\n"
                "• **Nitrogen Cycle:** Ensure your tank is fully cycled before introducing fish (Ammonia: 0ppm, Nitrite: 0ppm, Nitrate: <20ppm).\n"
                "• **Water Maintenance:** Perform 20-25% weekly water changes using dechlorinated water.\n"
                "• **Feeding:** Feed high-grade pellets or frozen daphnia only what can be consumed within 2 minutes."
            )

        # ── Diet / Nutrition ──
        elif any(w in msg_lower for w in ["diet", "food", "eat", "feed", "nutrition"]):
            return (
                "🍽️ **Multi-Species Nutrition Overview:**\n\n"
                "• **Dogs:** High-protein balanced kibble or wet food; avoid grapes, chocolate, and xylitol.\n"
                "• **Cats:** Strict carnivores — wet food recommended for hydration and kidney health.\n"
                "• **Birds:** Pellets + fresh vegetables + low seed intake.\n"
                "• **Reptiles/Lizards:** Live gut-loaded insects + leafy greens + calcium D3 powder.\n"
                "• **Rabbits:** 80% Timothy Hay + fresh greens.\n\n"
                "Ask me about any specific breed or species for custom feeding instructions!"
            )

        # ── Exercise / Enrichment ──
        elif any(w in msg_lower for w in ["exercise", "activity", "walk", "play", "enrichment"]):
            return (
                "🏃 **Activity & Enrichment Guide:**\n\n"
                "• **Dogs:** 45-60 min daily exercise, sniff walks, and puzzle toys.\n"
                "• **Cats:** 2-3 daily 15-min wand toy sessions + vertical cat trees.\n"
                "• **Birds:** 2-4 hours out-of-cage perching and foraging toys.\n"
                "• **Lizards/Reptiles:** Climbing branches, bio-active exploration, and gentle handling.\n"
                "• **Rabbits:** Evening free-roam play with cardboard tunnels."
            )

        # ── Exotic Pets ──
        elif any(w in msg_lower for w in ["exotic", "hedgehog", "sugar glider", "chinchilla", "ferret", "guinea pig", "hamster"]):
            return (
                "🌟 **Exotic & Small Mammal Care Guide:**\n\n"
                "**🦔 Hedgehogs:**\n"
                "• Maintain ambient temp 73-80°F (they attempt hibernation below 72°F — life-threatening!)\n"
                "• Feed high-quality cat kibble + mealworms, avoid dairy and citrus\n"
                "• Provide a running wheel (solid surface, not wire) for nightly exercise\n\n"
                "**🐹 Hamsters & Guinea Pigs:**\n"
                "• Guinea pigs need daily Vitamin C (they can't synthesize it) — bell peppers are excellent\n"
                "• Hamsters are solitary; guinea pigs are social and need a companion\n"
                "• Both need spacious enclosures (minimum 7.5 sq ft for guinea pigs)\n\n"
                "**🐿️ Sugar Gliders & Chinchillas:**\n"
                "• Sugar gliders are nocturnal and need a bonding pouch for socialization\n"
                "• Chinchillas require dust baths (never water baths!) and cool temps under 75°F\n\n"
                "Ask about any specific exotic pet for detailed care instructions! 🔍"
            )

        # ── Default Active Pet Response ──
        else:
            pet_name = "your active pet"
            species_str = ""
            if "Name: " in pet_context:
                try:
                    pet_name = pet_context.split("Name: ")[1].split("\n")[0]
                    species_val = pet_context.split("Species: ")[1].split("\n")[0]
                    breed_val = pet_context.split("Breed: ")[1].split("\n")[0]
                    species_str = f" ({species_val} - {breed_val})"
                except Exception:
                    pass

            return (
                f"🐾 **Haven Pet AI — Dedicated Assistant for {pet_name}:**\n\n"
                f"I provide personalized guidance tailored strictly for **{pet_name}**{species_str}.\n\n"
                f"• 🩺 **Health Check** — Describe any symptoms or behavior changes for immediate triage.\n"
                f"• 📷 **Breed & Species Identification** — Upload a photo using the camera button to analyze species and breed features.\n"
                f"• 🌟 **Care Recommendations** — Ask specific questions regarding {pet_name}'s health, environment, or vitality.\n\n"
                f"How can I assist with **{pet_name}** today? 💬"
            )

