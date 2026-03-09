"""game-schema: canonical Pydantic models for the WW2 Pacific 1940 2E referee system."""
from enums import (
    BattleStatus,
    ConfidenceBand,
    CorrectionType,
    DiceMode,
    EventType,
    Phase,
    PHASE_ORDER,
    Player,
    PLAYER_ORDER,
    UnitStatus,
    UnitType,
    VictoryStatus,
    ZoneType,
)
from game_state import (
    Audit,
    BattleParticipant,
    BattleRound,
    Economy,
    GameState,
    PendingBattle,
    PendingPlacement,
    TurnState,
    Unit,
    VisionReconciliationStatus,
    ZoneState,
)
from events import (
    AnyEvent,
    BaseEvent,
    BattleResolvedEvent,
    BattleRoundRolledEvent,
    BattleStartedEvent,
    CalibrationCompletedEvent,
    CasualtiesAssignedEvent,
    CombatDeclaredEvent,
    GameCreatedEvent,
    GameEndedEvent,
    IncomeCollectedEvent,
    ManualCorrectionAppliedEvent,
    MoveCommittedEvent,
    ObservationReceivedEvent,
    PhaseAdvancedEvent,
    PlacementCommittedEvent,
    ProposedStateGeneratedEvent,
    PurchaseCommittedEvent,
    RefereeOverrideEvent,
    RetreatDeclaredEvent,
    TurnEndedEvent,
)
from observation import (
    BoardTransform,
    BoundingBox,
    Detection,
    Mask,
    Observation,
    UncertaintyFlags,
    ZoneCandidate,
    ZoneObservation,
)
from bot import (
    ActionItem,
    BotSuggestion,
    BotSuggestionResponse,
    ScoreBreakdown,
    SimulationSummary,
)
from websocket_messages import (
    AnyWsMessage,
    BattleProgressMessage,
    CorrectionRequestedMessage,
    ErrorMessage,
    ObservationFrameMessage,
    PhaseChangedMessage,
    StateUpdatedMessage,
)

__all__ = [
    # enums
    "BattleStatus", "ConfidenceBand", "CorrectionType", "DiceMode",
    "EventType", "Phase", "PHASE_ORDER", "Player", "PLAYER_ORDER",
    "UnitStatus", "UnitType", "VictoryStatus", "ZoneType",
    # game state
    "Audit", "BattleParticipant", "BattleRound", "Economy", "GameState",
    "PendingBattle", "PendingPlacement", "TurnState", "Unit",
    "VisionReconciliationStatus", "ZoneState",
    # events
    "AnyEvent", "BaseEvent", "BattleResolvedEvent", "BattleRoundRolledEvent",
    "BattleStartedEvent", "CalibrationCompletedEvent", "CasualtiesAssignedEvent",
    "CombatDeclaredEvent", "GameCreatedEvent", "GameEndedEvent",
    "IncomeCollectedEvent", "ManualCorrectionAppliedEvent", "MoveCommittedEvent",
    "ObservationReceivedEvent", "PhaseAdvancedEvent", "PlacementCommittedEvent",
    "ProposedStateGeneratedEvent", "PurchaseCommittedEvent", "RefereeOverrideEvent",
    "RetreatDeclaredEvent", "TurnEndedEvent",
    # observation
    "BoardTransform", "BoundingBox", "Detection", "Mask", "Observation",
    "UncertaintyFlags", "ZoneCandidate", "ZoneObservation",
    # bot
    "ActionItem", "BotSuggestion", "BotSuggestionResponse",
    "ScoreBreakdown", "SimulationSummary",
    # websocket
    "AnyWsMessage", "BattleProgressMessage", "CorrectionRequestedMessage",
    "ErrorMessage", "ObservationFrameMessage", "PhaseChangedMessage",
    "StateUpdatedMessage",
]
