from enum import Enum
from typing import Dict, Optional, Callable, Any, Coroutine


class WeaponType(Enum):
    MUNDANE = 1
    MAGIC = 2


class VantageEnum(Enum):
    ADVANTAGE = 1
    DISADVANTAGE = 2
    NO = 3


class CurrentAttack:
    __instances: Dict[int, 'CurrentAttack'] = {}

    def __init__(self):
        self.stage: EAttackStageData = EAttackStage.NONE
        self.attacker: int = 0
        self.weapon_name: str = ""
        self.weapon: Optional[Weapon] = None
        self.tmp_hit: str = "0"
        self.vantage: VantageEnum = VantageEnum.NO
        self.tmp_damage: str = "0"
        self.button: bool = False
        self.hit_roll: int = 0
        self.damage_roll: int = 0
        self.hit: bool = False
        self.effects_to_roll: int = 1
        self.full_attack: bool = True

    def load_weapon(self, user: 'User') -> bool:
        self.weapon = user.get_weapon(self.weapon_name)
        return self.weapon is not None

    @staticmethod
    def reset_for(guild: int):
        CurrentAttack.__instances[guild] = CurrentAttack()

    @staticmethod
    def get_current_attack_for(guild: int) -> 'CurrentAttack':
        if guild not in CurrentAttack.__instances:
            CurrentAttack.__instances[guild] = CurrentAttack()
        return CurrentAttack.__instances[guild]


class Weapon:
    def __init__(self, weapon_type: WeaponType, to_hit: str = "0", damage: str = "0"):
        self.weapon_type: WeaponType = weapon_type
        self.uses: int = 0
        self.player_known: bool = False
        self.current_effect: int = 0
        self.to_hit: str = to_hit
        self.damage: str = damage

    def serialize(self):
        return {
            "weapon-type": self.weapon_type.value,
            "uses": self.uses,
            "player_known": self.player_known,
            "current_effect": self.current_effect,
            "to_hit": self.to_hit,
            "damage": self.damage
        }

    def deserialize(self, loaded_data: Dict[Any, Any]) -> 'Weapon':
        self.weapon_type = WeaponType(loaded_data["weapon-type"])
        self.uses = loaded_data["uses"]
        self.player_known = loaded_data["player_known"]
        self.current_effect = loaded_data["current_effect"]
        self.to_hit = loaded_data["to_hit"]
        self.damage = loaded_data["damage"]
        return self


class User:
    def __init__(self):
        self.__weapons: Dict[str, Weapon] = {}

    def get_weapon(self, name: str) -> Optional[Weapon]:
        name = name.lower()
        if name in self.__weapons:
            return self.__weapons[name]
        else:
            return None

    def get_weapons(self) -> Dict[str, Weapon]:
        return self.__weapons

    def add_weapon(self, name: str, weapon: Weapon):
        name = name.lower()
        if name in self.__weapons:
            raise WeaponDuplicationException("That weapon already exists")
        self.__weapons[name] = weapon

    def serialize(self):
        return {key: value.serialize() for (key, value) in self.__weapons.items()}

    def deserialize(self, loaded_data: Dict[Any, Any]) -> 'User':
        for key, value in loaded_data.items():
            self.__weapons[key] = Weapon(WeaponType.MAGIC).deserialize(value)
        return self


class WeaponDuplicationException(Exception):
    pass


class UserList:
    __instances: Dict[int, 'UserList'] = {}

    def __init__(self):
        self.__users: Dict[int, User] = {}

    def get_user(self, user_id: int) -> User:
        if user_id not in self.__users:
            self.__users[user_id] = User()
        return self.__users[user_id]

    def serialize(self):
        return {key: value.serialize() for (key, value) in self.__users.items()}

    def deserialize(self, loaded_data: Dict[Any, Any]) -> 'UserList':
        for key, value in loaded_data.items():
            self.__users[int(key)] = User().deserialize(value)
        return self

    @staticmethod
    def get_instances() -> Dict[int, 'UserList']:
        return UserList.__instances

    @staticmethod
    def get_list_for(guild: int) -> 'UserList':
        if guild not in UserList.__instances:
            UserList.__instances[guild] = UserList()
        return UserList.__instances[guild]

    @staticmethod
    def serialize_all():
        return {key: value.serialize() for (key, value) in UserList.__instances.items()}

    @staticmethod
    def deserialize_all(loaded_data: Dict[Any, Any]):
        for key, value in loaded_data.items():
            UserList.__instances[int(key)] = UserList().deserialize(value)


class EAttackStageData:
    def __init__(self, stage_num: id, author_only: bool, dice_roll: bool):
        if author_only and dice_roll:
            raise ValueError("An attack stage may not be both author_only and a dice roll")
        self.stage_num = stage_num
        self.author_only = author_only
        self.dice_roll = dice_roll


class EAttackStage:
    NONE = EAttackStageData(0, False, False)
    WEAPON_NAME = EAttackStageData(1, True, False)
    TEMP_HIT = EAttackStageData(2, True, False)
    VANTAGE = EAttackStageData(3, True, False)
    TEMP_DAMAGE = EAttackStageData(4, True, False)
    MUNDANE_BUTTON = EAttackStageData(5, True, False)
    ROLL_TO_HIT = EAttackStageData(6, False, True)
    DID_HIT = EAttackStageData(7, False, False)
    ROLL_DAMAGE = EAttackStageData(8, False, True)

    MAGIC_BUTTON = EAttackStageData(101, True, False)

    CHECK_CASCADE = EAttackStageData(201, False, True)
    ROLL_EFFECT = EAttackStageData(202, False, True)


class AttackStage:
    __instances: Dict[int, 'AttackStage'] = {}

    def __init__(self, prompt: Callable[[Any, CurrentAttack, User], Coroutine[Any, Any, None]],
                 respond: Callable[[Any, CurrentAttack, User], Coroutine[Any, Any, None]]):
        self.prompt = prompt
        self.respond = respond

    @staticmethod
    def register_stage(stage: EAttackStageData, attack_stage: 'AttackStage'):
        AttackStage.__instances[stage.stage_num] = attack_stage

    @staticmethod
    def get_stage(stage: EAttackStageData, is_attacker: bool = False, is_bot: bool = False) -> 'AttackStage':
        if stage.stage_num in AttackStage.__instances:
            if (not stage.author_only or is_attacker) and (not stage.dice_roll or is_bot):
                return AttackStage.__instances[stage.stage_num]
            else:
                return AttackStage(AttackStage.__instances[stage.stage_num].prompt, nop)
        else:
            return AttackStage(nop, nop)


async def nop(*_):
    pass
