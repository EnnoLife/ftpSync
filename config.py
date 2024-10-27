import json
from typing import Any, Callable

import yaml


class ProjectBaseConfig:
    def __init__(self, variables: dict[str, Any],
                 sub_initializer: Callable[[str, dict[str, Any]], bool] | None = None) -> None:
        for variable, value in variables.items():
            if isinstance(value, str):
                self.__setattr__(variable, value)
            elif isinstance(value, int):
                self.__setattr__(variable, value)
            elif isinstance(value, bool):
                self.__setattr__(variable, value)
            elif isinstance(value, list):
                self.__setattr__(variable, value)
            elif isinstance(value, dict):
                if sub_initializer is None or not sub_initializer(variable, value):
                    self.__setattr__(variable, value)

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def __str__(self) -> str:
        return self.to_json()


class FtpServerConfig(ProjectBaseConfig):
    host: str
    username: str
    password: str
    basedir: str
    blockSize: int

    def __init__(self, variables: dict[str, Any]) -> None:
        super().__init__(variables)


class Config(ProjectBaseConfig):
    ftpServer: FtpServerConfig
    targetDir: str

    def __init__(self, filename: str, variables: dict[str, Any]) -> None:
        super().__init__(variables, self.variable_initializer)

    @classmethod
    def from_yaml(cls, filename) -> 'Config':
        with open(filename, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
            return cls(filename, config_data)

    def variable_initializer(self, variable: str, value: Any) -> bool:
        if variable == 'ftpServer':
            self.ftpServer = FtpServerConfig(value)
            return True
        return False
