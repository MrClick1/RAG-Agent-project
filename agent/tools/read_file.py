from utils.path_tool import get_abs_path
from utils.config_handler import agent_conf



if __name__ == '__main__':
    external_data_path = get_abs_path(agent_conf["external_data_path"])

    with open(external_data_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            arr: list[str] = line.strip().split(",")
            arr[0]: str = arr[0].replace('"', "")
            print(arr[0])
