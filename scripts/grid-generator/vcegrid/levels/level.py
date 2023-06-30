from typing import List
import typing

if typing.TYPE_CHECKING:
    from ..triggers.trigger_generator import TriggerOrMetaTrigger


class TutorialInstruction:

    def __init__(
            self,
            message: str,
            step: int = None,
            lane_index_in_level: int = 0,
            offset_from_edge_start: float = 0,
            offset_from_edge_end: float = None,
            lateral_offset: float = 0
    ):
        """
        Instructions to be displayed as banners above the street, for example.

        :param message:
        :param step: Future legacy variable.
            Used in Unity to load the fitting tutorial banner prefab
        :param offset_from_edge_start: In meters.
        :param offset_from_edge_end: In meters;
            will only be used if offset_from_edge_start is None
        :param lateral_offset: In meters to the right.
        """
        self.message = message
        self.step = step
        self.lane_index_in_level = lane_index_in_level
        self.offset_from_edge_start = offset_from_edge_start
        self.offset_from_edge_end = offset_from_edge_end
        self.lateral_offset = lateral_offset


class Level:

    def __init__(
            self,
            difficulty: str,
            num_edges: int,
            meta_triggers: List['TriggerOrMetaTrigger'] = None,
            tutorial_instructions: List['TutorialInstruction'] = None
    ):
        self.difficulty = difficulty
        self.num_edges = num_edges
        self.meta_triggers = meta_triggers if meta_triggers is not None else []
        self.tutorial_instructions: List[TutorialInstruction] = (
            tutorial_instructions if tutorial_instructions is not None else []
        )
