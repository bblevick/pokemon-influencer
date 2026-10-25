"""Optional writer composition for the accepted battle/preparation layers.

Using this class adds host persistence only. It never enables hosted decisions
or changes the native ROM. The manifest checks remain those of BattleStore.
"""
from battle.store import BattleStore
from .store import ViralityMixin


class ViralityBattleStore(ViralityMixin,BattleStore):
    pass
