from remnawave import RemnawaveSDK
from config.dotenv import EnvConfig


def create_remnawave_client() -> RemnawaveSDK:
    paneldata = EnvConfig()
    token, base_url = paneldata.get_remnawave_data()
    return RemnawaveSDK(base_url=base_url, token=token)
