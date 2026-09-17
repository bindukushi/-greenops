"""
Shared constants for the simulated multi-cloud fleet. Extracted here (rather
than living inside app/routes/cloud.py) so both the HTTP routes and the
background live-streaming engine (app/services/live_engine.py) can import
them without creating a circular import.
"""

SERVER_IDS = ["AWS001", "AWS002", "AWS003", "AWS004", "AWS005", "AWS006"]

# Each provider operates in a distinct subset of regions with its own typical
# carbon-intensity profile (via REGION_CARBON_FACTORS in app/ml/carbon_engine.py),
# letting the platform produce a genuine "AWS vs Azure vs GCP" comparison.
PROVIDERS = {
    "AWS": {"label": "Amazon Web Services", "regions": ["ap-south-1", "us-east-1", "us-west-2"]},
    "Azure": {"label": "Microsoft Azure", "regions": ["eu-west-1", "eu-north-1"]},
    "GCP": {"label": "Google Cloud Platform", "regions": ["sa-east-1", "us-west-2", "ap-south-1"]},
}
PROVIDER_NAMES = list(PROVIDERS.keys())


def provider_for_region(region: str) -> str:
    for provider, cfg in PROVIDERS.items():
        if region in cfg["regions"]:
            return provider
    return "AWS"
