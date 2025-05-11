import yaml
import os
from dotenv import load_dotenv, dotenv_values
load_dotenv(".env", override=False)  # take environment variables from ..env.
print(f"setting environment variables: {dotenv_values('.env')}")

def load_nested_params(*params):
    root = os.getcwd()
    # print('root',root)
    env = os.environ.get("PY_ENVIRONMENT")
    # print('env',env)
    with open(os.path.join(root, 'backend/config', f"config-{env}.yaml"), "r", encoding="utf-8") as f:
        conf = yaml.safe_load(f)

    if params:
        for param in params:
            if param in conf:
                conf = conf[param]
            else:
                raise KeyError(f"{param} not found in config")

        return conf

