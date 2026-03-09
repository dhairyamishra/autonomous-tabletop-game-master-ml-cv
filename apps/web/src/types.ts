// Canonical frontend types, generated from the Pydantic schemas.

export type Player = "japan" | "usa" | "uk_pacific" | "anzac" | "china";
export type Phase =
  | "setup"
  | "purchase"
  | "combat_move"
  | "conduct_combat"
  | "non_combat_move"
  | "mobilize_new_units"
  | "collect_income"
  | "turn_end";
export type UnitType =
  | "infantry" | "artillery" | "armor"
  | "fighter" | "bomber"
  | "battleship" | "carrier" | "cruiser" | "destroyer" | "submarine" | "transport"
  | "industrial_complex" | "antiaircraft_gun";
export type UnitStatus = "active" | "damaged" | "mobilizing" | "retreating" | "sunk" | "destroyed";
export type BattleStatus =
  | "pending" | "in_progress"
  | "attacker_won" | "defender_won" | "attacker_retreated" | "drawn";
export type ConfidenceBand = "high" | "medium" | "low" | "very_low";
export type VictoryStatus = "in_progress" | "japan_wins" | "allies_win";
export type ZoneType = "land" | "sea";

export interface Unit {
  unit_id: string;
  unit_type: UnitType;
  owner: Player;
  zone_id: string;
  status: UnitStatus;
  hits_taken: number;
  has_moved: boolean;
  has_attacked: boolean;
  carried_by: string | null;
  carrying: string[];
}

export interface ZoneState {
  zone_id: string;
  owner: Player | null;
  ipc_value: number;
  units: string[];
  has_industrial_complex: boolean;
  industrial_complex_damage: number;
  is_capital: boolean;
  is_victory_city: boolean;
}

export interface Economy {
  treasury: Record<string, number>;
  income: Record<string, number>;
}

export interface BattleRound {
  round_number: number;
  attacker_rolls: number[];
  defender_rolls: number[];
  attacker_hits: number;
  defender_hits: number;
  attacker_casualties: string[];
  defender_casualties: string[];
}

export interface PendingBattle {
  battle_id: string;
  zone_id: string;
  attacker: Player;
  defender: Player;
  attacking_units: string[];
  defending_units: string[];
  rounds: BattleRound[];
  status: BattleStatus;
}

export interface TurnState {
  round: number;
  current_player: Player;
  phase: Phase;
}

export interface Audit {
  state_version: number;
  created_at: string;
  last_modified_at: string;
}

export interface GameState {
  game_id: string;
  scenario: string;
  ruleset_version: string;
  turn: TurnState;
  economy: Economy;
  zones: Record<string, ZoneState>;
  units: Record<string, Unit>;
  pending_battles: Record<string, PendingBattle>;
  victory_status: VictoryStatus;
  winner: Player | null;
  audit: Audit;
}

export interface BotActionItem {
  action_type: string;
  unit_id?: string;
  unit_type?: UnitType;
  from_zone?: string;
  to_zone?: string;
  count?: number;
  detail?: string;
}

export interface ScoreBreakdown {
  territory_value: number;
  expected_enemy_value_destroyed: number;
  expected_own_value_lost: number;
  positional_gain: number;
  capital_safety: number;
  follow_up_mobility: number;
  counterattack_risk: number;
  total: number;
}

export interface BotSuggestion {
  suggestion_id: string;
  rank: number;
  player: Player;
  phase: Phase;
  actions: BotActionItem[];
  score: number;
  score_breakdown: ScoreBreakdown;
  reasoning: string;
  confidence_band: ConfidenceBand;
  simulation_summary: SimulationSummary | null;
  warnings: string[];
}

// Vision / Observation types

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface ZoneCandidate {
  zone_id: string;
  confidence: number;
  overlap_fraction: number;
}

export interface Detection {
  detection_id: string;
  track_id: string | null;
  unit_type: UnitType | null;
  owner: Player | null;
  class_confidence: number;
  owner_confidence: number;
  overall_confidence: number;
  bbox: BoundingBox;
  centroid_board: number[] | null;
  zone_candidates: ZoneCandidate[];
  best_zone: string | null;
  is_occluded: boolean;
  is_stacked: boolean;
  occlusion_fraction: number;
  confidence_band: ConfidenceBand;
}

export interface ZoneObservation {
  zone_id: string;
  unit_counts: Record<string, number>;
  owner_candidates: Player[];
  total_detections: number;
  has_uncertainty: boolean;
  uncertainty_reasons: string[];
}

export interface BoardTransform {
  homography_matrix: number[][] | null;
  board_corners_image: number[][] | null;
  board_corners_board: number[][] | null;
  is_calibrated: boolean;
  calibrated_at: string | null;
  calibration_confidence: number;
}

export interface UncertaintyFlags {
  has_overlapping_units: boolean;
  has_occluded_units: boolean;
  has_low_confidence_class: boolean;
  has_unstable_tracks: boolean;
  has_impossible_count_jump: boolean;
  has_multiple_zone_candidates: boolean;
  flagged_zones: string[];
  flagged_detection_ids: string[];
}

export interface Observation {
  observation_id: string;
  game_id: string;
  session_id: string;
  frame_id: number;
  captured_at: string;
  processing_latency_ms: number;
  camera_id: string;
  board_transform: BoardTransform;
  is_calibrated: boolean;
  detections: Detection[];
  zone_observations: Record<string, ZoneObservation>;
  uncertainty_flags: UncertaintyFlags;
  overall_confidence: ConfidenceBand;
  requires_confirmation: boolean;
  confirmation_reasons: string[];
}

export interface SimulationSummary {
  simulations_run: number;
  win_probability: number;
  expected_attacker_losses: number;
  expected_defender_losses: number;
  ipc_swing: number;
}

// WebSocket messages
export type WsMessageType =
  | "state_updated"
  | "observation_frame"
  | "battle_progress"
  | "phase_changed"
  | "correction_requested"
  | "error"
  | "connected";

export interface WsMessage {
  type: WsMessageType;
  game_id?: string;
  session_id?: string;
  timestamp?: string;
  [key: string]: unknown;
}

export interface SessionInfo {
  session_id: string;
  game_id: string;
  player_assignments: Record<string, string>;
  current_player: string;
  current_phase: string;
  current_round: number;
}
