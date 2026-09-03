export interface Customer {
  id: string;
  name: string;
  email: string;
  phone?: string;
  total_orders: number;
  successful_orders: number;
  lifetime_value_inr: number;
}

export interface PaymentAttempt {
  id: string;
  provider_payment_id?: string;
  amount_inr: number;
  currency: string;
  method: string;
  status: "created" | "authorized" | "captured" | "failed" | "refunded";
  failure_code?: string;
  failure_reason?: string;
  created_at: string;
}

export interface Order {
  id: string;
  provider_order_id: string;
  amount_inr: number;
  currency: string;
  status: "created" | "attempted" | "paid" | "cancelled" | "expired";
  customer?: Customer;
  payment_attempts?: PaymentAttempt[];
  created_at: string;
}

export interface ScoreContribution {
  feature: string;
  points: number;
  explanation: string;
}

export interface RecoveryScoreResult {
  score: number;
  score_band: "HIGH" | "MEDIUM" | "LOW" | "VERY_LOW";
  failure_category: string;
  feature_contributions: Record<string, number>;
  explanation_summary: string;
  signals?: Record<string, any>;
}

export interface AgentProposal {
  diagnosis: string;
  diagnosis_category: string;
  recommended_action: string;
  confidence_score: number;
  decision_factors: string[];
  suggested_discount_pct: number;
  suggested_expiry_hours: number;
  metadata?: Record<string, any>;
}

export interface PolicyDecisionResult {
  decision: "ALLOW" | "BLOCK" | "ESCALATE";
  effective_action: string;
  policy_version: string;
  reason_codes: string[];
  human_readable_summary: string;
}

export interface RecoveryAction {
  id: string;
  opportunity_id: string;
  order_id?: string;
  order_amount_inr?: number;
  action_type: string;
  idempotency_key: string;
  policy_approved: boolean;
  execution_status: "PENDING" | "QUEUED" | "EXECUTING" | "SUCCEEDED" | "AMBIGUOUS" | "FAILED" | "CANCELLED";
  provider_action_id?: string;
  payment_link_url?: string;
  error_category?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface RecoveryOpportunity {
  id: string;
  merchant_id: string;
  order_id: string;
  status: "DETECTED" | "SCORING" | "EVALUATING" | "POLICY_GATING" | "EXECUTING" | "INTERVENED" | "RECOVERED" | "ESCALATED" | "CLOSED_UNRECOVERED";
  failure_category: string;
  recovery_score?: number;
  score_band?: string;
  revenue_at_risk_inr: number;
  recovered_amount_inr: number;
  attempt_count: number;
  order?: Order;
  actions?: RecoveryAction[];
  decisions?: any[];
  created_at: string;
  updated_at: string;
}

export interface AuditEvent {
  id: string;
  merchant_id?: string;
  event_type: string;
  actor_type: string;
  actor_id?: string;
  resource_type: string;
  resource_id: string;
  details?: Record<string, any>;
  created_at: string;
}

export interface MerchantPolicy {
  id: string;
  merchant_id: string;
  merchant_name: string;
  auto_recovery_enabled: boolean;
  policy_version: string;
  max_retry_attempts: number;
  cooldown_minutes: number;
  max_auto_recovery_amount_inr: number;
  min_score_threshold: number;
  allowed_actions: string[];
}

export interface BenchmarkMetrics {
  total_cases: number;
  revenue_at_risk_inr: number;
  recovery_attempts: number;
  attempt_rate: number;
  recovered_revenue_inr: number;
  recovery_rate: number;
  precision: number;
  recall: number;
  false_positive_amount_inr: number;
  net_recovered_value_inr: number;
  confusion_matrix?: {
    TP: number;
    FP: number;
    FN: number;
    TN: number;
  };
}

export interface FrontierPoint {
  threshold: number;
  recovery_attempts: number;
  attempt_rate: number;
  recovered_revenue_inr: number;
  recovery_rate: number;
  precision: number;
  recall: number;
  false_positive_amount_inr: number;
  net_recovered_value_inr: number;
  recovered_revenue_per_attempt: number;
  net_recovered_value_per_attempt: number;
}
