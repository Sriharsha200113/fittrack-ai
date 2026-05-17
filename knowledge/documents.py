"""
Fitness knowledge base for ChromaDB RAG.
Covers Indian food macros, nutrition science, exercise guides, and lifestyle.
"""

KNOWLEDGE_DOCS = [
    # ─── INDIAN FOOD MACROS ───────────────────────────────────────────────────

    {
        "id": "food_001",
        "text": "Chicken breast (100g, skinless, cooked) contains approximately 165 calories, 31g protein, 0g carbs, 3.6g fat. Gold standard protein source for muscle building and fat loss. Grilled or boiled is preferred. Boneless chicken thigh has more fat (~9g) but similar protein.",
        "metadata": {"type": "food", "tags": ["protein", "chicken", "non-veg"], "source": "nutrition_db"},
    },
    {
        "id": "food_002",
        "text": "Dal (cooked, 100g) contains approximately 116 calories, 9g protein, 20g carbs, 0.4g fat. Excellent plant-based protein and fiber source. Toor dal, moong dal, and masoor dal are most common. Best paired with rice or roti for complete amino acid profile.",
        "metadata": {"type": "food", "tags": ["protein", "veg", "dal", "fiber"], "source": "nutrition_db"},
    },
    {
        "id": "food_003",
        "text": "Paneer (100g) contains approximately 265 calories, 18g protein, 3g carbs, 20g fat. High in protein and calcium. Best protein source for vegetarians. Grilled or bhurji is better than fried. 250g paneer gives ~45g protein — roughly equivalent to 3 chicken breasts.",
        "metadata": {"type": "food", "tags": ["protein", "veg", "paneer", "dairy"], "source": "nutrition_db"},
    },
    {
        "id": "food_004",
        "text": "White rice (cooked, 100g) contains approximately 130 calories, 2.7g protein, 28g carbs, 0.3g fat. Fast-digesting carbohydrate, great for post-workout. Brown rice has the same calories but 3x more fiber and slightly more micronutrients. One standard cup cooked = 200g.",
        "metadata": {"type": "food", "tags": ["carbs", "rice", "post-workout"], "source": "nutrition_db"},
    },
    {
        "id": "food_005",
        "text": "Roti / Chapati (one piece, ~40g whole wheat) contains approximately 120 calories, 3.5g protein, 22g carbs, 2g fat. Whole wheat roti provides more fiber than maida. Two rotis with a cup of dal gives roughly 450 calories and 22g protein — a solid meal.",
        "metadata": {"type": "food", "tags": ["carbs", "roti", "wheat"], "source": "nutrition_db"},
    },
    {
        "id": "food_006",
        "text": "Eggs (one large egg) contain 78 calories, 6g protein, 0.6g carbs, 5g fat. Complete protein with all essential amino acids. 3 whole eggs = 18g protein, 225 calories. Egg whites only: 17 calories, 3.6g protein, negligible fat. Boiled or poached is best for fat loss.",
        "metadata": {"type": "food", "tags": ["protein", "eggs", "complete-protein"], "source": "nutrition_db"},
    },
    {
        "id": "food_007",
        "text": "Oats (100g dry) contain 389 calories, 17g protein, 66g carbs, 7g fat. High fiber, slow-digesting carbohydrate. One serving (40g dry = 80g cooked) gives 156 calories and 7g protein. Add protein powder or 2 eggs to boost protein to 30g+. Excellent breakfast for fat loss and satiety.",
        "metadata": {"type": "food", "tags": ["carbs", "fiber", "breakfast", "oats"], "source": "nutrition_db"},
    },
    {
        "id": "food_008",
        "text": "Chicken biryani (one serving ~300g) contains approximately 450-550 calories, 25-30g protein, 55-65g carbs, 12-18g fat. Higher calorie than plain chicken + rice due to ghee/oil. Portion control is critical. Raita on the side adds protein. Best consumed at lunch, not dinner for fat loss.",
        "metadata": {"type": "food", "tags": ["indian", "biryani", "mixed"], "source": "nutrition_db"},
    },
    {
        "id": "food_009",
        "text": "Greek yogurt (100g) contains 59 calories, 10g protein, 3.6g carbs, 0.4g fat. High-protein snack rich in probiotics. Plain curd (dahi, 100g) has 60 calories, 3.4g protein — Greek yogurt has nearly 3x more protein. Excellent pre-sleep protein or snack between meals.",
        "metadata": {"type": "food", "tags": ["protein", "dairy", "snack", "yogurt"], "source": "nutrition_db"},
    },
    {
        "id": "food_010",
        "text": "Banana (one medium, ~120g) contains 105 calories, 1.3g protein, 27g carbs, 0.4g fat. High in potassium and fast carbohydrates. Excellent pre-workout fuel — eat 30-45 minutes before training. Avoid as late-night snack during fat loss. Pairs well with protein shake post-workout.",
        "metadata": {"type": "food", "tags": ["carbs", "fruit", "pre-workout", "banana"], "source": "nutrition_db"},
    },
    {
        "id": "food_011",
        "text": "Almonds (28g, ~23 nuts) contain 164 calories, 6g protein, 6g carbs, 14g fat. High in healthy fats, vitamin E, and magnesium. Good fat loss snack — the fat promotes satiety. Don't overeat: 30g is a serving. Soaked almonds may have slightly better absorption.",
        "metadata": {"type": "food", "tags": ["nuts", "fat", "snack", "almonds"], "source": "nutrition_db"},
    },
    {
        "id": "food_012",
        "text": "Peanut butter (2 tbsp, 32g) contains 190 calories, 8g protein, 7g carbs, 16g fat. High calorie density — easy to overeat. Excellent source of healthy fats and protein. Use sparingly during fat loss. Pairs well with oats or roti. Choose natural (no added sugar) peanut butter.",
        "metadata": {"type": "food", "tags": ["fat", "protein", "peanut-butter", "nuts"], "source": "nutrition_db"},
    },
    {
        "id": "food_013",
        "text": "Salmon (100g, cooked) contains 208 calories, 20g protein, 0g carbs, 13g fat. Excellent omega-3 fatty acid source (EPA/DHA) which reduces inflammation and supports muscle recovery. Expensive but nutritionally superior to most protein sources. 2-3 servings per week is ideal.",
        "metadata": {"type": "food", "tags": ["protein", "fish", "omega-3", "non-veg"], "source": "nutrition_db"},
    },
    {
        "id": "food_014",
        "text": "Curd / Dahi (100g whole milk) contains 61 calories, 3.4g protein, 4.7g carbs, 3.3g fat. Probiotic-rich. Low-fat dahi reduces calories to ~40 per 100g with similar protein. Common in Indian meals. Raita (curd + vegetables) is a great low-calorie side dish and protein boost.",
        "metadata": {"type": "food", "tags": ["dairy", "probiotic", "veg", "curd"], "source": "nutrition_db"},
    },
    {
        "id": "food_015",
        "text": "Moong sprouts (100g) contain 30 calories, 3g protein, 4g carbs, 0.2g fat. Extremely low calorie, high in fiber and micronutrients. Sprouting increases bioavailability of protein and vitamins. Excellent snack for fat loss. Add lemon and chaat masala for flavor.",
        "metadata": {"type": "food", "tags": ["veg", "sprouts", "low-calorie", "fiber"], "source": "nutrition_db"},
    },
    {
        "id": "food_016",
        "text": "Sweet potato (100g, baked) contains 90 calories, 2g protein, 21g carbs, 0.1g fat. Complex carbohydrate with lower glycemic index than white potato. Rich in beta-carotene and potassium. Good pre-workout carb source. One medium sweet potato (~200g) = 180 calories.",
        "metadata": {"type": "food", "tags": ["carbs", "sweet-potato", "fiber"], "source": "nutrition_db"},
    },
    {
        "id": "food_017",
        "text": "Idli (one piece, ~40g) contains 39 calories, 2g protein, 8g carbs, 0.1g fat. Very low calorie, fermented food with probiotics. 4 idlis = 156 calories. Sambar adds protein and fiber. Excellent for fat loss breakfast. Coconut chutney adds ~50-80 calories per serving.",
        "metadata": {"type": "food", "tags": ["south-indian", "carbs", "low-calorie", "idli"], "source": "nutrition_db"},
    },
    {
        "id": "food_018",
        "text": "Dosa (one plain dosa, ~65g) contains 120 calories, 3g protein, 22g carbs, 2.5g fat. Similar to idli but slightly higher calorie due to oil on griddle. Masala dosa adds potato filling (~+100 calories). Sambar dosa is nutritionally better than masala dosa for fat loss.",
        "metadata": {"type": "food", "tags": ["south-indian", "carbs", "dosa"], "source": "nutrition_db"},
    },
    {
        "id": "food_019",
        "text": "Sambar (100ml) contains 45 calories, 2.5g protein, 7g carbs, 1g fat. High in fiber, vitamins, and protein from lentils. Excellent accompaniment to idli/dosa/rice. The tamarind and spices boost metabolism. Three cups sambar adds only 135 calories with ~7g protein.",
        "metadata": {"type": "food", "tags": ["south-indian", "protein", "veg", "sambar"], "source": "nutrition_db"},
    },
    {
        "id": "food_020",
        "text": "Rajma (cooked kidney beans, 100g) contains 127 calories, 8.7g protein, 22g carbs, 0.5g fat. Excellent plant protein and fiber source. High in iron. Rajma chawal is a complete protein meal — rice provides the amino acids missing in rajma. Best for lunch, not dinner.",
        "metadata": {"type": "food", "tags": ["protein", "veg", "rajma", "legumes"], "source": "nutrition_db"},
    },
    {
        "id": "food_021",
        "text": "Chole / Chickpeas (cooked, 100g) contain 164 calories, 8.9g protein, 27g carbs, 2.6g fat. High fiber legume — keeps you full for hours. Rich in iron, folate, and plant protein. Bhature adds significant calories (~300+ per piece). Chole with roti is the leaner option.",
        "metadata": {"type": "food", "tags": ["protein", "veg", "chole", "chickpeas"], "source": "nutrition_db"},
    },
    {
        "id": "food_022",
        "text": "Whey protein (one scoop, ~30g) contains approximately 110-130 calories, 24-27g protein, 2-4g carbs, 1-2g fat. Fast-absorbing protein ideal post-workout. Not a food replacement — supplement to bridge protein gaps. One scoop in water is sufficient. Milk adds ~90 calories.",
        "metadata": {"type": "food", "tags": ["supplement", "protein", "whey", "post-workout"], "source": "nutrition_db"},
    },
    {
        "id": "food_023",
        "text": "Tofu (firm, 100g) contains 76 calories, 8g protein, 1.9g carbs, 4.8g fat. Good plant protein for vegans. Absorb flavor from marinades well. Pan-fry with minimal oil or add to curries. 200g tofu bhurji with vegetables = ~200 calories and 16g protein.",
        "metadata": {"type": "food", "tags": ["veg", "vegan", "protein", "tofu"], "source": "nutrition_db"},
    },
    {
        "id": "food_024",
        "text": "Spinach (100g raw) contains 23 calories, 2.9g protein, 3.6g carbs, 0.4g fat. Very low calorie, high in iron, calcium, and vitamins A, C, K. Add to smoothies, stir-fries, dal. 200g raw spinach shrinks to ~50g cooked. Pair with vitamin C (lemon) to increase iron absorption.",
        "metadata": {"type": "food", "tags": ["veg", "low-calorie", "greens", "spinach"], "source": "nutrition_db"},
    },
    {
        "id": "food_025",
        "text": "Broccoli (100g) contains 34 calories, 2.8g protein, 7g carbs, 0.4g fat. High in fiber, vitamin C, and calcium. Low calorie and filling. Steam or stir-fry — don't boil as it destroys nutrients. Add to pulao or stir-fry for volume eating during fat loss.",
        "metadata": {"type": "food", "tags": ["veg", "low-calorie", "greens", "broccoli"], "source": "nutrition_db"},
    },
    {
        "id": "food_026",
        "text": "Mutton / Goat meat (cooked, 100g) contains 294 calories, 25g protein, 0g carbs, 21g fat. Higher fat than chicken. Rich in iron, zinc, and B12. Best consumed 1-2 times per week. Choose lean cuts and remove visible fat. Mutton curry has additional oil — total dish can be 350-500 calories per serving.",
        "metadata": {"type": "food", "tags": ["non-veg", "protein", "mutton"], "source": "nutrition_db"},
    },
    {
        "id": "food_027",
        "text": "Rohu fish (cooked, 100g) contains 97 calories, 17g protein, 0g carbs, 3g fat. Lean protein source common in Bengali/North Indian cooking. Lower omega-3 than salmon but much cheaper. Fish curry typically adds 100-150 calories per serving from oil and coconut milk.",
        "metadata": {"type": "food", "tags": ["non-veg", "protein", "fish", "low-fat"], "source": "nutrition_db"},
    },
    {
        "id": "food_028",
        "text": "Cottage cheese / Chenna (100g) contains 98 calories, 11g protein, 3g carbs, 4.3g fat. High protein, moderate calorie dairy. Often confused with paneer — cottage cheese has lower fat. Good low-calorie protein source. Mix with fruit for a balanced snack.",
        "metadata": {"type": "food", "tags": ["dairy", "protein", "veg", "cottage-cheese"], "source": "nutrition_db"},
    },
    {
        "id": "food_029",
        "text": "Poha (cooked, 100g) contains 130 calories, 2.3g protein, 27g carbs, 1.5g fat. Light and easy-to-digest breakfast carbohydrate. Add peas, peanuts, and vegetables to boost nutrition. One bowl poha with nuts = ~200 calories, 7g protein. Better than paratha for fat loss mornings.",
        "metadata": {"type": "food", "tags": ["carbs", "breakfast", "indian", "poha"], "source": "nutrition_db"},
    },
    {
        "id": "food_030",
        "text": "Cucumber (100g) contains 15 calories, 0.7g protein, 3.6g carbs, 0.1g fat. Almost pure water — excellent for hydration and volume eating. Eat unlimited during fat loss. Pairs well with hummus, curd, or lemon for a satisfying snack at near-zero calories.",
        "metadata": {"type": "food", "tags": ["veg", "low-calorie", "hydration", "cucumber"], "source": "nutrition_db"},
    },

    # ─── NUTRITION PRINCIPLES ─────────────────────────────────────────────────

    {
        "id": "nutrition_001",
        "text": "For fat loss, maintain a caloric deficit of 300-500 calories below your TDEE. Aggressive deficits above 750 calories risk muscle loss. Prioritize protein at 1.6-2.2g per kg bodyweight to preserve muscle. Losing 0.5-0.75kg per week is the sustainable fat loss rate.",
        "metadata": {"type": "nutrition", "tags": ["fat_loss", "deficit", "protein"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_002",
        "text": "For muscle gain (bulk), eat at a caloric surplus of 200-400 calories above TDEE. Protein target: 1.6-2.2g per kg bodyweight. Gaining 0.25-0.5kg per week is optimal — faster gains mean excess fat. Carbohydrates fuel workouts and replenish glycogen stores.",
        "metadata": {"type": "nutrition", "tags": ["muscle_gain", "surplus", "bulk"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_003",
        "text": "Body recomposition (recomp) — gaining muscle while losing fat — is possible at maintenance calories. Most effective for beginners, those returning after a break, or those at high body fat (>20%). Requires very high protein (2g/kg+) and consistent progressive overload training.",
        "metadata": {"type": "nutrition", "tags": ["recomp", "maintenance", "protein"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_004",
        "text": "Protein timing: distribute protein intake across 3-5 meals (30-40g per meal) for optimal muscle protein synthesis. Post-workout protein within 2 hours is beneficial but total daily protein is the primary driver of muscle growth. Don't skip protein at breakfast.",
        "metadata": {"type": "nutrition", "tags": ["protein", "timing", "muscle_synthesis"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_005",
        "text": "Hydration: drink 35-45ml per kg bodyweight daily (3-4 liters for 80kg person). Dehydration of just 2% reduces athletic performance by up to 20%. Drink 500ml 1-2 hours pre-workout. Urine color is the best guide — pale yellow is ideal, dark yellow means drink more.",
        "metadata": {"type": "nutrition", "tags": ["hydration", "water", "performance"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_006",
        "text": "Pre-workout meal (1.5-2 hours before training): moderate carbs + protein, low fat. Examples: banana + whey shake, oats + milk + protein, 2 rotis + dal, rice + chicken. Avoid high-fat meals before training — fat slows gastric emptying and causes sluggishness.",
        "metadata": {"type": "nutrition", "tags": ["pre-workout", "meal-timing", "carbs"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_007",
        "text": "Post-workout nutrition: consume 30-40g protein and 50-60g carbohydrates within 2 hours. Best options: rice + chicken, whey protein + banana, eggs + roti. The post-workout window enhances glycogen replenishment and muscle protein synthesis. Don't train fasted without planning protein intake.",
        "metadata": {"type": "nutrition", "tags": ["post-workout", "recovery", "glycogen"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_008",
        "text": "Calorie tracking accuracy: home-cooked Indian food is hard to estimate. Dal (1 cup = ~300ml) is ~250 calories. Rice (1 cup cooked = ~200g) is ~260 calories. Roti (one piece) is ~120 calories. Sabzi with oil is ~100-150 calories per portion. Always slightly overestimate portions.",
        "metadata": {"type": "nutrition", "tags": ["tracking", "indian", "estimation"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_009",
        "text": "Eating for fat loss without feeling deprived: eat protein first at every meal (it activates satiety hormones). Fill half your plate with vegetables. Use spices freely (no calories). Prioritize whole foods over processed. Drink water before meals to reduce hunger.",
        "metadata": {"type": "nutrition", "tags": ["fat_loss", "satiety", "habits"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_010",
        "text": "Cheat meals vs cheat days: one cheat meal per week is sustainable and helps adherence. A full cheat day can easily add 1000-2000+ extra calories, erasing the entire week's deficit. Plan your cheat meal — eat slowly, enjoy it, and return to your plan next meal.",
        "metadata": {"type": "nutrition", "tags": ["cheat-meal", "adherence", "fat_loss"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_011",
        "text": "Protein sources ranked by bioavailability (PDCAAS score): whey protein (1.0), eggs (1.0), chicken (0.92), milk (1.0), soy (1.0), beef (0.92), kidney beans (0.68), wheat (0.40). Animal proteins are generally more bioavailable. Vegans should combine legumes + grains.",
        "metadata": {"type": "nutrition", "tags": ["protein", "bioavailability", "vegans"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_012",
        "text": "Alcohol and fitness: one standard drink slows muscle protein synthesis for 24-48 hours. Beer (330ml) has ~150 calories and slows fat burning. Occasional drinking won't ruin progress, but regular drinking significantly impairs recovery, hormone levels, and sleep quality.",
        "metadata": {"type": "nutrition", "tags": ["alcohol", "fat_loss", "recovery"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_013",
        "text": "Fat loss plateau: after 4-6 weeks of dieting, metabolism adapts (metabolic adaptation). Solutions: 2-week diet break at maintenance, increase NEAT (non-exercise activity thermogenesis), add 30-min walks, or further reduce calories by 100-150. Avoid dramatic changes.",
        "metadata": {"type": "nutrition", "tags": ["plateau", "fat_loss", "metabolism"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_014",
        "text": "Insulin and fat storage: refined carbs (sugar, maida, white bread) spike insulin sharply, promoting fat storage if in a surplus. However, insulin is not the enemy — it also drives amino acids into muscles. Total calorie balance matters more than insulin spikes for fat loss.",
        "metadata": {"type": "nutrition", "tags": ["insulin", "carbs", "fat_loss", "myth-busting"], "source": "nutrition_science"},
    },
    {
        "id": "nutrition_015",
        "text": "Belly fat is not spot-reducible. You cannot lose fat from a specific area by doing crunches. Overall calorie deficit causes whole-body fat loss. The belly and love handles are often the last areas to lean out, especially for men. Patience and consistency is the only solution.",
        "metadata": {"type": "nutrition", "tags": ["belly-fat", "spot-reduction", "myth-busting"], "source": "nutrition_science"},
    },

    # ─── EXERCISE GUIDES ─────────────────────────────────────────────────────

    {
        "id": "exercise_001",
        "text": "For fat loss, combine resistance training (3-4 days/week) with cardio (2-3 days/week). Resistance training preserves muscle and elevates metabolism for 24-48 hours post-workout (EPOC effect). HIIT cardio burns more calories per minute than steady-state. Never do only cardio — it leads to muscle loss.",
        "metadata": {"type": "exercise", "tags": ["fat_loss", "cardio", "resistance"], "source": "exercise_science"},
    },
    {
        "id": "exercise_002",
        "text": "For muscle gain, prioritize progressive overload: systematically increase weight, reps, or sets. Train each muscle group 2x per week for maximum hypertrophy. Compound movements (bench, squat, deadlift, overhead press, rows) build the most mass. Track every workout.",
        "metadata": {"type": "exercise", "tags": ["muscle_gain", "progressive_overload", "compound"], "source": "exercise_science"},
    },
    {
        "id": "exercise_003",
        "text": "Chest workout essentials: bench press (flat, incline, decline), dumbbell flyes, cable crossovers, push-ups. Incline bench press emphasizes upper chest. 3-4 sets of 8-12 reps per exercise for hypertrophy (muscle building). 5-6 reps of heavier weight builds more strength. Rest 2-3 minutes between sets.",
        "metadata": {"type": "exercise", "tags": ["chest", "workout", "hypertrophy"], "source": "exercise_science"},
    },
    {
        "id": "exercise_004",
        "text": "Back workout essentials: deadlifts (overall thickness), pull-ups/lat pulldowns (width), barbell rows, seated cable rows, face pulls (rear delts). Always initiate pulls from the lats, not arms. Back responds well to high volume. Include both vertical (pull-ups) and horizontal (rows) pulling.",
        "metadata": {"type": "exercise", "tags": ["back", "workout", "deadlift"], "source": "exercise_science"},
    },
    {
        "id": "exercise_005",
        "text": "Leg workout essentials: squats (king of exercises — hits quads, hamstrings, glutes simultaneously), leg press, Romanian deadlifts (hamstrings), leg curls, lunges, calf raises. Never skip legs — lower body training boosts testosterone and overall growth by up to 25%.",
        "metadata": {"type": "exercise", "tags": ["legs", "squat", "workout"], "source": "exercise_science"},
    },
    {
        "id": "exercise_006",
        "text": "Cardio calorie burn per 30 minutes (~80kg person): running at 8km/h (350 kcal), cycling moderate (280 kcal), swimming (300 kcal), jump rope (400 kcal), brisk walk 6km/h (150 kcal), HIIT (300-450 kcal), stair climbing (250 kcal). Heavier people burn more.",
        "metadata": {"type": "exercise", "tags": ["cardio", "calories", "fat_loss"], "source": "exercise_science"},
    },
    {
        "id": "exercise_007",
        "text": "Sleep is the most underrated recovery tool. Growth hormone is primarily released during deep sleep (slow wave sleep). Aim for 7-9 hours. Sleep deprivation increases cortisol (muscle breakdown, fat storage) and reduces testosterone by 10-15% after one week of poor sleep.",
        "metadata": {"type": "exercise", "tags": ["sleep", "recovery", "hormones"], "source": "health_science"},
    },
    {
        "id": "exercise_008",
        "text": "5-day workout split for muscle gain: Day 1 Chest, Day 2 Back, Day 3 Shoulders, Day 4 Arms (Biceps + Triceps), Day 5 Legs. Rest or active recovery Day 6-7. Each muscle gets 1 dedicated session + indirect work from other days. Good for intermediate lifters.",
        "metadata": {"type": "exercise", "tags": ["split", "5-day", "muscle_gain", "schedule"], "source": "exercise_science"},
    },
    {
        "id": "exercise_009",
        "text": "Push-pull-legs (PPL) split: Push day (chest, shoulders, triceps), Pull day (back, biceps), Leg day. Run 2x per week for 6 training days. Best split for intermediate-to-advanced lifters wanting high frequency. Each muscle gets trained 2x per week for maximum hypertrophy stimulus.",
        "metadata": {"type": "exercise", "tags": ["split", "PPL", "muscle_gain", "schedule"], "source": "exercise_science"},
    },
    {
        "id": "exercise_010",
        "text": "HIIT (High-Intensity Interval Training): alternate 20-40 seconds max effort with 10-20 seconds rest for 15-25 minutes. Examples: sprint-walk intervals, burpees, jump squats. Burns more fat per minute than steady-state cardio and elevates metabolism for hours after. Do 2-3x per week maximum.",
        "metadata": {"type": "exercise", "tags": ["HIIT", "cardio", "fat_loss", "intervals"], "source": "exercise_science"},
    },
    {
        "id": "exercise_011",
        "text": "Shoulder workout essentials: overhead press (barbell or dumbbell — primary mass builder), lateral raises (side delts), front raises, face pulls (rear delts, critical for joint health), Arnold press. Train all three heads. Shoulders recover quickly — can be trained 2-3x per week.",
        "metadata": {"type": "exercise", "tags": ["shoulders", "workout", "delts"], "source": "exercise_science"},
    },
    {
        "id": "exercise_012",
        "text": "Arm workout: Biceps — barbell curls, hammer curls, incline dumbbell curls (full stretch = more muscle). Triceps — close grip bench press, skull crushers, tricep pushdowns, overhead extension. Triceps make up 2/3 of arm size — prioritize them for bigger arms.",
        "metadata": {"type": "exercise", "tags": ["arms", "biceps", "triceps", "workout"], "source": "exercise_science"},
    },
    {
        "id": "exercise_013",
        "text": "Core training: planks (60-90 sec holds), dead bugs, cable crunches, hanging leg raises, ab wheel rollouts. Core is about stability and anti-rotation, not just crunches. A strong core protects the lower back during heavy compound lifts. Train core 3x per week.",
        "metadata": {"type": "exercise", "tags": ["core", "abs", "workout", "stability"], "source": "exercise_science"},
    },
    {
        "id": "exercise_014",
        "text": "Warm-up before training: 5-10 minutes light cardio, then 2-3 warm-up sets with 50-60% of working weight. Never jump straight to heavy weights — injury risk is high. Dynamic stretching before (leg swings, arm circles). Static stretching after (hold 30-60 seconds per muscle).",
        "metadata": {"type": "exercise", "tags": ["warm-up", "injury-prevention", "mobility"], "source": "exercise_science"},
    },
    {
        "id": "exercise_015",
        "text": "Beginner gym program: Start with 3 days per week full body. Key exercises: squat, bench press, rows, overhead press, Romanian deadlift. Do 3 sets of 8-12 reps each. Add weight weekly when you can complete all sets cleanly. Spend 3 months building the foundation before splitting.",
        "metadata": {"type": "exercise", "tags": ["beginner", "full-body", "program"], "source": "exercise_science"},
    },

    # ─── LIFESTYLE & RECOVERY ─────────────────────────────────────────────────

    {
        "id": "lifestyle_001",
        "text": "NEAT (Non-Exercise Activity Thermogenesis) — the calories burned from daily movement outside formal exercise. Walking, cooking, typing, fidgeting all count. NEAT can vary by 500-1000 calories per day between sedentary and active people. Taking 8,000-10,000 steps per day significantly aids fat loss.",
        "metadata": {"type": "lifestyle", "tags": ["NEAT", "fat_loss", "activity"], "source": "health_science"},
    },
    {
        "id": "lifestyle_002",
        "text": "Stress management for fitness: chronic stress elevates cortisol, which promotes abdominal fat storage and muscle breakdown. Meditation, deep breathing, limiting phone use before bed, and cold showers reduce cortisol. High stress negates training gains even if diet and sleep are perfect.",
        "metadata": {"type": "lifestyle", "tags": ["stress", "cortisol", "recovery", "hormones"], "source": "health_science"},
    },
    {
        "id": "lifestyle_003",
        "text": "Weight fluctuations are normal and do not represent actual fat change. Day-to-day weight can vary by 1-3kg due to water retention, sodium intake, carb storage, digestive contents, and hormones. Weigh yourself every morning after toilet, compare weekly averages, not daily numbers.",
        "metadata": {"type": "lifestyle", "tags": ["weight-tracking", "fat_loss", "mindset"], "source": "health_science"},
    },
    {
        "id": "lifestyle_004",
        "text": "Muscle memory: if you've been fit before, regaining lost muscle takes much less time than building it initially. Muscle nuclei (myonuclei) persist even after muscle atrophy. After 2-4 weeks off, expect some strength loss but full recovery typically happens in 4-8 weeks of training.",
        "metadata": {"type": "lifestyle", "tags": ["muscle-memory", "recovery", "motivation"], "source": "health_science"},
    },
    {
        "id": "lifestyle_005",
        "text": "Consistency over intensity: training 3 days per week for a full year beats training 6 days a week for 3 months then quitting. The best workout is the one you actually do. Build habits, not just motivation. Start small, be consistent, increase intensity gradually.",
        "metadata": {"type": "lifestyle", "tags": ["consistency", "habits", "motivation"], "source": "health_science"},
    },
    {
        "id": "lifestyle_006",
        "text": "Creatine monohydrate: the most researched and effective legal supplement. 3-5g daily (no loading needed) increases strength by 5-15% and muscle size over time. Safe for kidneys in healthy individuals. Doesn't cause hair loss (despite myths). No cycling needed — take daily.",
        "metadata": {"type": "lifestyle", "tags": ["creatine", "supplement", "muscle_gain", "strength"], "source": "health_science"},
    },
    {
        "id": "lifestyle_007",
        "text": "How to lose belly fat fast: there is no shortcut. Belly fat requires overall fat loss via calorie deficit. Reduce sodium (less bloating), increase fiber (reduces hunger), drink more water, add 30 min of walking daily, prioritize sleep, and manage stress. Results in 8-12 weeks of consistency.",
        "metadata": {"type": "lifestyle", "tags": ["belly-fat", "fat_loss", "practical"], "source": "health_science"},
    },
    {
        "id": "lifestyle_008",
        "text": "Morning vs evening workouts: no significant difference in muscle gain or fat loss — best time is when you'll actually do it consistently. Morning workouts improve adherence (fewer schedule conflicts). Evening workouts have slightly higher strength and body temperature. Hormones are more favorable for strength in late afternoon.",
        "metadata": {"type": "lifestyle", "tags": ["timing", "workout", "adherence"], "source": "health_science"},
    },
    {
        "id": "lifestyle_009",
        "text": "Protein shake timing myths: 'anabolic window' is not as narrow as once believed. Post-workout protein within 2-3 hours is ideal but the total daily protein is what drives muscle growth. Protein shake is just a convenient food — real food works equally well if macros are met.",
        "metadata": {"type": "lifestyle", "tags": ["protein", "timing", "myth-busting", "supplement"], "source": "health_science"},
    },
    {
        "id": "lifestyle_010",
        "text": "How to eat at Indian restaurants and stay on track: order grilled/tandoori (less oil), ask for dal over heavy gravies, choose roti over naan (naan has butter), avoid biryani or eat half portions, skip the starters (pappadam, samosa), drink water not juice/soda.",
        "metadata": {"type": "lifestyle", "tags": ["eating-out", "indian", "fat_loss", "practical"], "source": "health_science"},
    },
]
