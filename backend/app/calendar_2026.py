SEASON = 2026

RACES: list[dict] = [
    {
        "slug": "im-new-zealand",
        "title": "ANZCO Foods IRONMAN New Zealand",
        "date": "2026-03-07",
        "distance": "im",
        "is_world_championship": False,
        "max_points": 5000,
        "eligible_gender": "both",
    },
    {
        "slug": "im703-geelong",
        "title": "IRONMAN 70.3 Geelong",
        "date": "2026-03-22",
        "distance": "im703",
        "is_world_championship": False,
        "max_points": 2500,
        "eligible_gender": "both",
    },
    {
        "slug": "im703-oceanside",
        "title": "IRONMAN 70.3 Oceanside",
        "date": "2026-03-28",
        "distance": "im703",
        "is_world_championship": False,
        "max_points": 2500,
        "eligible_gender": "both",
    },
    {
        "slug": "im-texas",
        "title": "IRONMAN Texas",
        "date": "2026-04-18",
        "distance": "im",
        "is_world_championship": False,
        "max_points": 5000,
        "eligible_gender": "both",
    },
    {
        "slug": "im703-aix-en-provence",
        "title": "IRONMAN 70.3 Aix-en-Provence",
        "date": "2026-05-17",
        "distance": "im703",
        "is_world_championship": False,
        "max_points": 2500,
        "eligible_gender": "both",
    },
    {
        "slug": "im-hamburg",
        "title": "IRONMAN Hamburg",
        "date": "2026-06-07",
        "distance": "im",
        "is_world_championship": False,
        "max_points": 5000,
        "eligible_gender": "W",
    },
    {
        "slug": "im703-pennsylvania",
        "title": "IRONMAN 70.3 Pennsylvania",
        "date": "2026-06-14",
        "distance": "im703",
        "is_world_championship": False,
        "max_points": 2500,
        "eligible_gender": "both",
    },
    {
        "slug": "im703-elsinore",
        "title": "IRONMAN 70.3 Elsinore",
        "date": "2026-06-21",
        "distance": "im703",
        "is_world_championship": False,
        "max_points": 2500,
        "eligible_gender": "both",
    },
    {
        "slug": "im-frankfurt",
        "title": "IRONMAN Frankfurt",
        "date": "2026-06-28",
        "distance": "im",
        "is_world_championship": False,
        "max_points": 5000,
        "eligible_gender": "M",
    },
    {
        "slug": "im703-swansea",
        "title": "IRONMAN 70.3 Swansea",
        "date": "2026-07-12",
        "distance": "im703",
        "is_world_championship": False,
        "max_points": 2500,
        "eligible_gender": "both",
    },
    {
        "slug": "im-lake-placid",
        "title": "IRONMAN Lake Placid",
        "date": "2026-07-19",
        "distance": "im",
        "is_world_championship": False,
        "max_points": 5000,
        "eligible_gender": "both",
    },
    {
        "slug": "im703-boise",
        "title": "IRONMAN 70.3 Boise",
        "date": "2026-07-25",
        "distance": "im703",
        "is_world_championship": False,
        "max_points": 2500,
        "eligible_gender": "both",
    },
    {
        "slug": "im-kalmar",
        "title": "IRONMAN Kalmar",
        "date": "2026-08-15",
        "distance": "im",
        "is_world_championship": False,
        "max_points": 5000,
        "eligible_gender": "both",
    },
    {
        "slug": "im703-zell-am-see",
        "title": "IRONMAN 70.3 Zell am See",
        "date": "2026-08-30",
        "distance": "im703",
        "is_world_championship": False,
        "max_points": 2500,
        "eligible_gender": "both",
    },
    {
        "slug": "im703-world-championship-w",
        "title": "IRONMAN 70.3 World Championship",
        "date": "2026-09-12",
        "distance": "im703",
        "is_world_championship": True,
        "max_points": 3000,
        "eligible_gender": "W",
    },
    {
        "slug": "im703-world-championship-m",
        "title": "IRONMAN 70.3 World Championship",
        "date": "2026-09-13",
        "distance": "im703",
        "is_world_championship": True,
        "max_points": 3000,
        "eligible_gender": "M",
    },
    {
        "slug": "im-world-championship",
        "title": "IRONMAN World Championship",
        "date": "2026-10-10",
        "distance": "im",
        "is_world_championship": True,
        "max_points": 6000,
        "eligible_gender": "both",
    },
]

# Published pro start lists for the remaining World Championship races. Each page
# has one table per gender (bib prefix ``F`` / ``M``); ``races`` maps that prefix
# to the seed race slug it gates. Once a list is scraped, that race only enters
# the ceiling of athletes who appear on it.
START_LISTS: list[dict] = [
    {
        "url": (
            "https://www.ironman.com/stories/pro-elite/start-list-2026-precision"
            "-fuel-hydration-ironman-703-world-championship-nice"
        ),
        "races": {
            "W": "im703-world-championship-w",
            "M": "im703-world-championship-m",
        },
    },
    {
        "url": (
            "https://www.ironman.com/stories/pro-elite/start-list-2026-ironman-"
            "world-championship-mens-race-kailua-kona"
        ),
        "races": {"M": "im-world-championship"},
    },
    {
        "url": (
            "https://www.ironman.com/stories/pro-elite/start-list-2026-ironman-"
            "world-championship-womens-race-kailua-kona"
        ),
        "races": {"W": "im-world-championship"},
    },
]
