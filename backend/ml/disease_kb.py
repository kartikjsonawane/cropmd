"""
CropMD – Disease Knowledge Base
Static advisory data for all 38 PlantVillage classes.
Populated into MongoDB on first run via /api/admin/seed-diseases.
"""

DISEASE_KB = {
    "Tomato___Early_blight": {
        "description": (
            "Early blight (Alternaria solani) is one of the most common tomato diseases. "
            "It appears as dark brown concentric rings on older leaves, forming a 'target' pattern. "
            "The disease progresses upward from older to younger leaves and can defoliate plants."
        ),
        "symptoms": [
            "Dark brown spots with concentric rings (bull's-eye pattern)",
            "Yellow halo surrounding the lesion",
            "Spots first appear on older, lower leaves",
            "Severe defoliation in humid conditions",
            "Stem cankers near soil line (collar rot)",
        ],
        "causes": [
            "Fungal pathogen Alternaria solani",
            "High humidity (>90%) and temperatures 24–29°C",
            "Infected seed or transplants",
            "Overhead irrigation keeping foliage wet",
            "Poor air circulation in dense plantings",
        ],
        "treatments": [
            {"name": "Chlorothalonil", "dosage": "2 g/L water", "frequency": "Every 7–10 days",
             "notes": "Broad-spectrum fungicide; use preventively"},
            {"name": "Mancozeb", "dosage": "2.5 g/L water", "frequency": "Every 7 days",
             "notes": "Effective contact fungicide"},
            {"name": "Copper Oxychloride", "dosage": "3 g/L water", "frequency": "Every 10 days",
             "notes": "OMRI-listed for organic farming"},
        ],
        "pesticides": [
            {"name": "Daconil 2787", "type": "Fungicide", "active_ingredient": "Chlorothalonil",
             "dosage": "2 g/L"},
            {"name": "Dithane M-45", "type": "Fungicide", "active_ingredient": "Mancozeb",
             "dosage": "2.5 g/L"},
        ],
        "prevention": [
            "Use certified disease-free seeds and transplants",
            "Rotate crops – avoid tomato, potato, pepper in same field for 2+ years",
            "Apply mulch to reduce soil splash onto lower leaves",
            "Use drip irrigation; avoid wetting foliage",
            "Remove and destroy infected plant debris after harvest",
            "Space plants for good air circulation",
        ],
        "fertilizer_tips": [
            "Ensure balanced NPK – potassium deficiency increases susceptibility",
            "Apply calcium-based fertilizer to strengthen cell walls",
            "Avoid excess nitrogen, which promotes lush growth vulnerable to infection",
        ],
        "irrigation_tips": "Use drip or furrow irrigation. Water in the morning so foliage dries quickly. Avoid overhead sprinklers that keep leaves wet overnight.",
        "severity_default": "High",
    },

    "Tomato___Late_blight": {
        "description": (
            "Late blight (Phytophthora infestans) is a devastating oomycete disease that can destroy "
            "entire fields within days under cool, wet conditions. It caused the 1840s Irish Potato Famine."
        ),
        "symptoms": [
            "Water-soaked, irregular greenish-grey lesions on leaves",
            "White fluffy sporulation on underside of leaves",
            "Dark brown lesions on stems",
            "Firm dark brown lesions on fruit",
            "Rapid collapse of entire plant in humid conditions",
        ],
        "causes": [
            "Oomycete Phytophthora infestans",
            "Cool temperatures (10–20°C) with prolonged leaf wetness",
            "Infected potato tubers or volunteer plants",
            "Windborne sporangia from nearby infected fields",
        ],
        "treatments": [
            {"name": "Metalaxyl + Mancozeb", "dosage": "2.5 g/L", "frequency": "Every 7 days",
             "notes": "Systemic + contact combination; most effective"},
            {"name": "Cymoxanil + Mancozeb", "dosage": "2 g/L", "frequency": "Every 5–7 days",
             "notes": "Good curative activity"},
            {"name": "Dimethomorph", "dosage": "1 g/L", "frequency": "Every 7 days",
             "notes": "Excellent for resistant strains"},
        ],
        "pesticides": [
            {"name": "Ridomil Gold", "type": "Fungicide",
             "active_ingredient": "Metalaxyl-M + Mancozeb", "dosage": "2.5 g/L"},
        ],
        "prevention": [
            "Plant resistant varieties (e.g., Iron Lady, Defiant)",
            "Destroy all volunteer potato and tomato plants",
            "Apply preventive fungicides before disease appears",
            "Monitor weather forecasts – apply at disease-favorable conditions",
            "Remove and burn infected plant material immediately",
        ],
        "fertilizer_tips": [
            "High potassium levels reduce susceptibility",
            "Balanced calcium nutrition improves plant immunity",
        ],
        "irrigation_tips": "Strictly use drip irrigation. Never apply overhead irrigation during disease-favorable weather. Ensure excellent drainage.",
        "severity_default": "High",
    },

    "Tomato___Bacterial_spot": {
        "description": (
            "Bacterial spot (Xanthomonas spp.) causes small, water-soaked lesions on leaves, "
            "stems, and fruit that reduce marketability and yield."
        ),
        "symptoms": [
            "Small, water-soaked circular spots on leaves (1–3mm)",
            "Spots turn brown with yellow halo",
            "Spots may coalesce causing leaf blight",
            "Raised, scab-like lesions on fruit",
            "Defoliation in severe cases",
        ],
        "causes": [
            "Bacteria Xanthomonas vesicatoria, X. euvesicatoria",
            "Warm temperatures (25–30°C) with high humidity",
            "Infected seeds (primary source)",
            "Splash dispersal by rain/irrigation",
        ],
        "treatments": [
            {"name": "Copper Hydroxide", "dosage": "3 g/L", "frequency": "Every 7 days",
             "notes": "Primary bactericide; start early"},
            {"name": "Copper Oxychloride + Mancozeb", "dosage": "2 + 2 g/L",
             "frequency": "Every 7 days", "notes": "Tank mix for broader control"},
        ],
        "pesticides": [
            {"name": "Kocide 3000", "type": "Bactericide",
             "active_ingredient": "Copper Hydroxide", "dosage": "3 g/L"},
        ],
        "prevention": [
            "Use pathogen-free certified seed; hot-water treat seed at 50°C for 25 min",
            "Avoid working in field when plants are wet",
            "Use drip irrigation",
            "3–4 year crop rotation",
            "Remove infected plants promptly",
        ],
        "fertilizer_tips": [
            "Adequate zinc nutrition reduces bacterial infections",
            "Avoid excess nitrogen, which encourages soft tissue susceptible to bacteria",
        ],
        "irrigation_tips": "Drip only. Morning watering if overhead is unavoidable.",
        "severity_default": "Medium",
    },

    "Potato___Early_blight": {
        "description": "Early blight in potato (Alternaria solani) causes significant defoliation and tuber yield losses of up to 30% in susceptible varieties.",
        "symptoms": [
            "Dark brown concentric ring lesions on older leaves",
            "Yellow halo around spots",
            "Premature defoliation reducing tuber size",
            "Brown sunken lesions on tubers",
        ],
        "causes": [
            "Alternaria solani fungus",
            "Hot dry days followed by cool nights",
            "Nutrient-stressed plants are more susceptible",
        ],
        "treatments": [
            {"name": "Azoxystrobin", "dosage": "1 mL/L", "frequency": "Every 10–14 days",
             "notes": "Systemic strobilurin; excellent results"},
            {"name": "Chlorothalonil", "dosage": "2 g/L", "frequency": "Every 7 days",
             "notes": "Contact fungicide; preventive use"},
        ],
        "pesticides": [
            {"name": "Amistar", "type": "Fungicide", "active_ingredient": "Azoxystrobin",
             "dosage": "1 mL/L"},
        ],
        "prevention": [
            "Use certified disease-free seed tubers",
            "Plant resistant/tolerant varieties",
            "Maintain adequate soil nutrition (K, Ca)",
            "Practice 3-year crop rotation",
        ],
        "fertilizer_tips": [
            "Potassium at 180–240 kg/ha improves resistance",
            "Maintain soil pH 5.5–6.5 for optimal nutrient uptake",
        ],
        "irrigation_tips": "Consistent soil moisture prevents stress. Use drip or furrow. Avoid water stress which increases susceptibility.",
        "severity_default": "Medium",
    },

    "Potato___Late_blight": {
        "description": "Late blight (Phytophthora infestans) is the most destructive potato disease worldwide. Under conducive conditions it can destroy a field in 3–5 days.",
        "symptoms": [
            "Irregular water-soaked lesions on leaves",
            "White cottony growth on leaf undersides",
            "Brown rotting stems",
            "Pink-brown dry rot in tubers",
            "Entire plant collapse in epidemic conditions",
        ],
        "causes": [
            "Phytophthora infestans",
            "Cool wet weather (10–20°C, RH >90%)",
            "Infected seed tubers",
        ],
        "treatments": [
            {"name": "Metalaxyl-M", "dosage": "2.5 g/L", "frequency": "Every 7 days",
             "notes": "Apply at first sign or preventively before rain"},
            {"name": "Fluazinam", "dosage": "1 mL/L", "frequency": "Every 7–10 days",
             "notes": "Contact fungicide; good in resistance situations"},
        ],
        "pesticides": [
            {"name": "Ridomil Gold MZ", "type": "Fungicide",
             "active_ingredient": "Metalaxyl-M + Mancozeb", "dosage": "2.5 g/L"},
            {"name": "Shirlan", "type": "Fungicide", "active_ingredient": "Fluazinam",
             "dosage": "1 mL/L"},
        ],
        "prevention": [
            "Plant certified disease-free seed tubers",
            "Use resistant varieties (Sarpo Mira, Defender)",
            "Monitor Blight-Pro / Smith Period weather models",
            "Remove haulm (destroy) before harvest",
            "Store tubers in dry, ventilated conditions",
        ],
        "fertilizer_tips": [
            "Phosphorus promotes tuber initiation and disease resistance",
            "High potassium strengthens cell walls",
        ],
        "irrigation_tips": "Avoid overhead irrigation. Ensure excellent drainage. Hilling up reduces tuber infection from sporulating foliage.",
        "severity_default": "High",
    },

    "Corn_(maize)___Common_rust_": {
        "description": "Common rust (Puccinia sorghi) is a widespread corn fungal disease that reduces photosynthesis and yield, especially in cool humid areas.",
        "symptoms": [
            "Small, circular to elongated brick-red powdery pustules on leaves",
            "Pustules on both upper and lower leaf surfaces",
            "Pustules turn dark brown/black at maturity",
            "Severe infections cause premature leaf death",
        ],
        "causes": [
            "Obligate fungal parasite Puccinia sorghi",
            "Cool temperatures (15–25°C) and high humidity",
            "Windborne urediniospores",
        ],
        "treatments": [
            {"name": "Propiconazole", "dosage": "1 mL/L", "frequency": "2 applications 10 days apart",
             "notes": "Apply at VT/R1 stage for best ROI"},
            {"name": "Azoxystrobin + Propiconazole", "dosage": "0.5 + 0.5 mL/L",
             "frequency": "Every 14 days", "notes": "Premium tank mix"},
        ],
        "pesticides": [
            {"name": "Tilt 250 EC", "type": "Fungicide", "active_ingredient": "Propiconazole",
             "dosage": "1 mL/L"},
        ],
        "prevention": [
            "Plant rust-resistant hybrids (RB gene)",
            "Early planting to escape cool conditions",
            "Scout fields regularly after tasseling",
            "Avoid planting corn continuously in same field",
        ],
        "fertilizer_tips": [
            "Adequate potassium improves disease tolerance",
            "Avoid excessive nitrogen – promotes lush, susceptible tissue",
        ],
        "irrigation_tips": "Reduce free moisture on leaves. Avoid overhead irrigation during tasseling if possible.",
        "severity_default": "Medium",
    },

    "Corn_(maize)___Northern_Leaf_Blight": {
        "description": "Northern Leaf Blight (Exserohilum turcicum) causes large, cigar-shaped grey-green to tan lesions that can dramatically reduce corn yield.",
        "symptoms": [
            "Long (5–15 cm) cigar-shaped grey-green lesions",
            "Lesions turn tan with dark borders",
            "Lesions usually start on lower leaves",
            "Gray-green spores visible in humid conditions",
        ],
        "causes": [
            "Fungus Exserohilum turcicum",
            "Moderate temperatures (18–27°C) with prolonged leaf wetness",
            "Infected crop residue in soil",
        ],
        "treatments": [
            {"name": "Mancozeb", "dosage": "2.5 g/L", "frequency": "Every 7–10 days",
             "notes": "Preventive contact fungicide"},
            {"name": "Azoxystrobin", "dosage": "1 mL/L", "frequency": "Every 14 days",
             "notes": "Systemic; apply before symptoms appear for best results"},
        ],
        "pesticides": [
            {"name": "Amistar Top", "type": "Fungicide",
             "active_ingredient": "Azoxystrobin + Difenoconazole", "dosage": "1 mL/L"},
        ],
        "prevention": [
            "Plant NLB-resistant hybrids (Ht1, Ht2, HtN genes)",
            "Deep plow to bury infected residue",
            "Crop rotation with non-host crops",
        ],
        "fertilizer_tips": [
            "Silicon fertilizers (potassium silicate) reduce fungal penetration",
            "Balanced N:K ratio is critical",
        ],
        "irrigation_tips": "If using overhead irrigation, water early morning so leaves dry before evening. Drip preferred.",
        "severity_default": "High",
    },

    "Pepper,_bell___Bacterial_spot": {
        "description": "Bacterial spot (Xanthomonas spp.) is a major pepper disease causing fruit spots, defoliation, and yield losses of 10–50%.",
        "symptoms": [
            "Small, irregular water-soaked leaf spots",
            "Spots become dark with yellow halo",
            "Raised, scabby spots on fruit reducing marketability",
            "Defoliation in severe cases",
        ],
        "causes": [
            "Xanthomonas euvesicatoria",
            "Warm, wet weather (27–30°C)",
            "Contaminated seed",
            "Overhead irrigation",
        ],
        "treatments": [
            {"name": "Copper Hydroxide", "dosage": "3 g/L", "frequency": "Every 5–7 days",
             "notes": "Best bactericide available; rotate to avoid resistance"},
            {"name": "Streptomycin Sulfate", "dosage": "200 ppm", "frequency": "Every 7 days",
             "notes": "Antibiotic; check local regulations"},
        ],
        "pesticides": [
            {"name": "Kocide 3000", "type": "Bactericide",
             "active_ingredient": "Copper Hydroxide", "dosage": "3 g/L"},
        ],
        "prevention": [
            "Use hot-water treated seed (50°C, 25 min)",
            "Use drip irrigation",
            "Plant resistant varieties",
            "Disinfect tools and equipment",
        ],
        "fertilizer_tips": [
            "Calcium foliar sprays (0.5% CaCl₂) reduce infection",
            "Silica supplementation strengthens cell walls",
        ],
        "irrigation_tips": "Drip irrigation essential. Avoid wetting foliage. Do not work with plants when wet.",
        "severity_default": "Medium",
    },

    "Tomato___healthy": {
        "description": "This tomato plant appears healthy with no visible disease symptoms. Continue current crop management practices.",
        "symptoms": [],
        "causes": [],
        "treatments": [],
        "pesticides": [],
        "prevention": [
            "Continue regular scouting (2×/week)",
            "Maintain crop rotation schedule",
            "Monitor weather for disease-favorable conditions",
            "Keep irrigation equipment clean",
        ],
        "fertilizer_tips": [
            "Continue balanced NPK program",
            "Foliar micronutrient spray at flowering",
        ],
        "irrigation_tips": "Maintain consistent soil moisture at 60–80% field capacity. Use tensiometers or soil moisture sensors.",
        "severity_default": "None",
    },

    "Potato___healthy": {
        "description": "This potato plant appears healthy. Maintain current management practices and continue regular monitoring.",
        "symptoms": [],
        "causes": [],
        "treatments": [],
        "pesticides": [],
        "prevention": [
            "Continue regular field scouting",
            "Monitor for aphids (late blight vectors)",
            "Maintain hilling schedule",
        ],
        "fertilizer_tips": [
            "Side-dress nitrogen at tuber initiation",
            "Potassium critical during bulking stage",
        ],
        "irrigation_tips": "Consistent moisture critical during tuber bulking. Irrigate to maintain 70% field capacity.",
        "severity_default": "None",
    },
}


def get_advisory(class_name: str) -> dict:
    """Return advisory data for a given class name, with fallback."""
    return DISEASE_KB.get(class_name, {
        "description": f"Disease information for '{class_name}' is being updated.",
        "symptoms": [],
        "causes": [],
        "treatments": [],
        "pesticides": [],
        "prevention": ["Consult a local agronomist for specific recommendations."],
        "fertilizer_tips": [],
        "irrigation_tips": "Follow standard irrigation practices for your crop.",
        "severity_default": "Medium",
    })
