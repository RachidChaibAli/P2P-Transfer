import random

ADJECTIVES = [
    "Red", "Blue", "Green", "Golden", "Silver", "Bright", "Cosmic", "Silent",
    "Swift", "Brave", "Calm", "Clever", "Gentle", "Happy", "Lucky", "Sunny",
    "Wild", "Amber", "Crystal", "Ruby", "Shadow", "Velvet", "Frosty", "Neon"
]

NOUNS = [
    "Strawberry", "Mango", "Falcon", "Panda", "Fox", "Otter", "Wolf", "Tiger",
    "Eagle", "Dolphin", "Koala", "Hawk", "Badger", "Owl", "Lynx", "Bear",
    "Cheetah", "Robin", "Sparrow", "Comet", "Pixel", "Wave", "Forest", "Star"
]


def generate_display_name() -> str:
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    tag = random.randint(1000, 9999)
    return f"{adj} {noun}#{tag}"

