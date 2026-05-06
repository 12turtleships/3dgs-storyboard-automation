# =============================================================================
# STORY BIBLE — "TREE"
# =============================================================================
# Single source of truth for all 19 scenes.
# Every scene generation script imports from here to ensure consistency
# across WHO, WHERE, WHEN, WHAT, WHY, and HOW.
# =============================================================================

# -----------------------------------------------------------------------------
# HOW — Visual Style
# Storyboard illustration, NOT photorealistic, NOT live actors/scenes.
# Semi-painterly digital art: clean linework, expressive figures,
# highly detailed natural elements. Cinematic composition. Warm paper grain.
# -----------------------------------------------------------------------------

STYLE_SUFFIX = (
    "Storyboard illustration style, not photorealistic, no live actors. "
    "Semi-painterly digital art with clean linework, expressive human figures, "
    "and highly detailed natural elements especially trees and light. "
    "Rich summer color palette: deep greens, warm stone, golden light. "
    "Cinematic composition with dramatic depth and layered foreground-midground-background. "
    "Visible brushwork, warm paper grain, film grain overlay. "
    "Conveys mood and emotion through light, color, posture, and scale. "
    "Animated pre-visualization quality. Clear storytelling in a single frame."
)

# -----------------------------------------------------------------------------
# WHO — Characters
# Consistent visual descriptions referenced in every shot they appear in.
# -----------------------------------------------------------------------------

WHO = {
    "zara": (
        "Zara: young woman, early 20s, medium build, dark brown shoulder-length hair often in a "
        "practical ponytail, gold-rimmed round academic glasses, wearing a worn faded grey hoodie, "
        "jeans, and slightly scuffed white canvas sneakers. "
        "Posture tracks her arc: early scenes — spine curved, shoulders hunched, head angled down. "
        "Late scenes — spine straight, shoulders open, chin level, walking with intention."
    ),
    "students": (
        "Background university students, ages 18-24, diverse group. "
        "All uniformly slouched with heads bowed down to glowing smartphone screens. "
        "Faces lit identically by screen glow regardless of individuality. "
        "Moving by rote muscle memory, zero eye contact with surroundings or each other. "
        "Backpacks, hoodies, mixed casual university attire."
    ),
    "professor": (
        "Professor: 50s-60s, salt-and-pepper hair, calm observant demeanor. "
        "Linen blazer in warm brown or cream, wire-rimmed glasses, weathered hands. "
        "Carries an old leather journal. Speaks in measured cadences. "
        "Presence suggests witness, not authority — watching more than directing."
    ),
    "tree": (
        "The Tree: an ancient English Oak (Quercus robur), 80-100 feet tall, "
        "trunk 12+ feet in diameter with deep charcoal-grey bark, heavily furrowed, "
        "patches of lichen and moss near the base. "
        "Massive broad spreading canopy — umbrella-like, not spire-like. "
        "Lush dense deep emerald-green summer leaves, so thick sunlight creates "
        "dappled cathedral light beneath. "
        "Feels older than the campus itself. Monolithic, immobile, permanent. "
        "The most detailed and lovingly rendered element in every frame."
    ),
}

# -----------------------------------------------------------------------------
# WHERE — Locations
# All five spatial zones of the campus. Consistent descriptions for prompts.
# -----------------------------------------------------------------------------

WHERE = {
    "courtyard": (
        "Central university courtyard: large open stone square, ancient cobblestones in grey and tan "
        "worn smooth by decades of foot traffic. The massive ancient oak tree stands at the center, "
        "its trunk and canopy dominating the space. Five pathways radiate outward from the courtyard. "
        "Surrounding three sides: warm stone Gothic and modernist university buildings, ivy-covered walls, "
        "tall arched windows. A few weathered benches around the tree perimeter, usually empty. "
        "Tree roots crack and lift the cobblestones — nature reclaiming human space."
    ),
    "pathways": (
        "Campus pathways: wide cobblestone walkways radiating from the central courtyard, "
        "5-15 feet wide, lined with ivy-covered stone walls, arched windows, ornamental lampposts. "
        "Worn moss on north-facing surfaces. Visual rhythm of window-wall-window-stone. "
        "Perspective lines from any pathway lead the eye back toward the central tree. "
        "Steady bidirectional flow of students — toward classes one direction, toward campus exit the other."
    ),
    "classroom": (
        "University computer classroom interior: rows of desks with desktop computers and laptops, "
        "harsh fluorescent overhead lighting, polished concrete floor. "
        "Large tall windows (8-10 feet high) on one wall reveal the campus courtyard and tree outside — "
        "ignored by everyone inside. Screen glow on students' faces. "
        "Visually cold, artificial, climate-controlled. "
        "The tree and summer daylight are barely visible through the windows, a world apart."
    ),
    "playground": (
        "Open recreational field adjacent to the courtyard: large green grass area, "
        "lush summer lawn rolling slightly, dotted with a few small trees far shorter than the oak. "
        "Scattered benches, a small shelter pavilion, sports markings on the grass. "
        "Direct sightline back to the great tree from any point in the field. "
        "Full sun exposure, minimal shade. Beautiful and open — theoretically for joy and play."
    ),
    "under_tree": (
        "The space directly beneath the oak's canopy: cool shadow, dappled green-gold light filtering "
        "from thousands of leaves above. Massive gnarled roots rising 2-3 feet from the earth, "
        "creating natural contours and seating zones. Compacted earth and moss underfoot. "
        "Acoustic quiet — outside campus sounds muffled beneath the canopy. "
        "Intimate despite being in the center of a public campus. "
        "Color palette shifts warmer here: green light through leaves, amber where sun breaks through."
    ),
}

# -----------------------------------------------------------------------------
# WHEN — Time Groups
# Lighting conditions by time of day. Summer throughout.
# -----------------------------------------------------------------------------

WHEN = {
    "early_morning": (
        "Early morning, 7-9 AM. Low-angle golden side-light, long shadows across the courtyard. "
        "Soft warm directional light, slight dew quality in the air. "
        "Clear bright blue sky. The tree is dramatically side-lit, trunk texture and bark fully visible."
    ),
    "mid_morning": (
        "Mid-morning, 9 AM - 12 PM. Sun rising higher, shadows shorter, light more direct. "
        "Bright, sharp, high-contrast summer daylight. Brilliant deep blue sky. "
        "Tree canopy brightly lit from above; shadows define the root system below."
    ),
    "afternoon": (
        "Midday to early afternoon, 12-3 PM. High overhead sun, near-vertical rays. "
        "Intense, direct light; minimal shadow angles; clinical brightness. "
        "Sky whitened by intense summer sun. Tree canopy glows rich green; "
        "shade beneath the tree is deepest and most dramatic."
    ),
    "golden_hour": (
        "Late afternoon golden hour, 3-5:30 PM. Sun lowering, warming, lengthening shadows. "
        "Warm amber-gold directional light. Deepening blue sky. "
        "Tree trunk glows with amber warmth; leaf edges backlit; cathedral canopy effect intensifies."
    ),
    "evening": (
        "Evening, 5:30-7:30 PM. Soft diffused light, warm orange, very long shadows. "
        "Sky transitioning to warm orange fading to deeper blue. "
        "Tree becomes a silhouette against the warm sky; internal canopy glows backlit. "
        "Magical, contemplative quality."
    ),
}

# -----------------------------------------------------------------------------
# WHAT — Story Synopsis
# One-sentence synopsis and act structure for reference.
# -----------------------------------------------------------------------------

WHAT = {
    "synopsis": (
        "A university student discovers an ancient oak tree in the campus courtyard that awakens her "
        "from smartphone addiction, teaching her that awareness itself is an act of freedom — "
        "and that the hardest part is choosing to stay awake."
    ),
    "act_1": "Scenes 1-6: Establish the beautiful campus and monolithic tree; introduce students as phone-zombies.",
    "act_2": "Scenes 7-14: Zara wakes up — sees the tree, walks the campus with new eyes, sits beneath it.",
    "act_3": "Scenes 15-19: The conscious choice — Zara picks the phone back up, but differently.",
    "tree_symbol": (
        "The Tree as monolith: silent non-communicating intelligence that awakens consciousness. "
        "Ancient, rooted, permanent witness — everything a smartphone is not."
    ),
}

# -----------------------------------------------------------------------------
# WHY — Theme
# -----------------------------------------------------------------------------

WHY = {
    "theme": (
        "In a world engineered to fragment attention, the act of choosing to pay attention — "
        "to actually see what is in front of you — is an act of freedom."
    ),
    "zara_why": (
        "Zara's name echoes Zarathustra. She is not the prophet but the first to hear the call. "
        "Ordinary, not predetermined — her awakening is universal and repeatable."
    ),
    "ending_why": (
        "Students pick their phones back up by choice, not compulsion. "
        "Real freedom is not the absence of temptation but the presence of choice. "
        "Awareness doesn't eliminate the phone — it changes the relationship to it."
    ),
}

# -----------------------------------------------------------------------------
# HOW — Camera Motifs
# Recurring angle/movement vocabulary. Reference in prompt descriptions.
# -----------------------------------------------------------------------------

HOW = {
    "worms_eye": (
        "Extreme low angle worm's-eye view looking up — emphasizes scale of tree against sky, "
        "human insignificance against ancient natural scale. Recurring motif for awe and revelation."
    ),
    "overhead": (
        "High bird's-eye or overhead establishing view looking down at campus — "
        "shows campus as organism, tree as hub, pathways as web. "
        "Godlike perspective, outside-observer view."
    ),
    "eye_level": (
        "Eye-level tracking through campus at character height — "
        "audience enters character's perceptual state. "
        "Early: unfocused, mechanical. Late: sharp, aware, discovering."
    ),
    "slow_push": (
        "Slow camera push-in toward subject — intimacy, focus, emotional weight. "
        "Used for realization beats and moments of stillness."
    ),
    "rack_focus": (
        "Rack focus from smartphone screen (sharp) to world beyond (soft) to world (sharp) — "
        "physically represents the shift in consciousness and attention."
    ),
    "foreground_frame": (
        "Every composition uses layered depth: foreground (tree element or architectural detail), "
        "midground (human figures), background (sky or buildings). "
        "No flat shots — depth teaches the eye to look into images."
    ),
}


# -----------------------------------------------------------------------------
# Helper: build a full prompt from components
# -----------------------------------------------------------------------------

def build_prompt(narrative: str, visual: str, characters: str, lighting_key: str, tone: str) -> str:
    """
    Assemble a consistent scene prompt from its five components plus the
    WHEN lighting block and the global STYLE_SUFFIX.

    Args:
        narrative:   What is happening in this beat (1 sentence).
        visual:      Composition, depth, spatial arrangement (2-3 sentences).
        characters:  Where characters are and their visible state (1-2 sentences).
        lighting_key: Key into WHEN dict (e.g. 'early_morning', 'afternoon').
        tone:        What the viewer should feel (1 sentence).
    """
    lighting = WHEN.get(lighting_key, "")
    return " ".join(filter(None, [narrative, visual, characters, lighting, tone, STYLE_SUFFIX]))
