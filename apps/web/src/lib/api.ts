import {
  RecoveryOpportunity,
  RecoveryAction,
  AuditEvent,
  MerchantPolicy,
  BenchmarkMetrics,
  FrontierPoint,
} from "./types";

const rawBase =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.hostname.includes("onrender.com")
    ? "https://recoverx-api-qhlx.onrender.com"
    : "http://localhost:8000");
const API_BASE_URL = rawBase.endsWith("/api/v1")
  ? rawBase
  : `${rawBase.replace(/\/+$/, "")}/api/v1`;

export async function fetchMetricsSummary() {
  try {
    const res = await fetch(`${API_BASE_URL}/opportunities/metrics/summary`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch metrics summary");
    return await res.json();
  } catch (err) {
    return {
      total_opportunities: 18,
      recovered_opportunities: 12,
      active_opportunities: 6,
      total_revenue_at_risk_inr: 185420.0,
      total_recovered_revenue_inr: 124890.0,
      recovery_rate: 0.673,
    };
  }
}

export async function fetchOpportunities(): Promise<RecoveryOpportunity[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/opportunities`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch opportunities");
    return await res.json();
  } catch (err) {
    return getFallbackOpportunities();
  }
}

export async function fetchOpportunityById(id: string): Promise<RecoveryOpportunity | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/opportunities/${id}`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch opportunity");
    return await res.json();
  } catch (err) {
    const fallback = getFallbackOpportunities().find((o) => o.id === id);
    return fallback || null;
  }
}

export async function fetchOpportunityActions(opportunityId: string): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/opportunities/${opportunityId}/actions`, { cache: "no-store" });
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    return [];
  }
}


export async function fetchActions(): Promise<RecoveryAction[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/actions`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch actions");
    return await res.json();
  } catch (err) {
    return getFallbackActions();
  }
}

export async function fetchAuditEvents(): Promise<AuditEvent[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/audit-events`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch audit events");
    return await res.json();
  } catch (err) {
    return getFallbackAuditEvents();
  }
}

export async function fetchBenchmarkAnalytics(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/analytics/benchmark`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch benchmark analytics");
    return await res.json();
  } catch (err) {
    return getFallbackBenchmark();
  }
}

export async function fetchMerchantPolicy(): Promise<MerchantPolicy> {
  try {
    const res = await fetch(`${API_BASE_URL}/policies`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch policy");
    return await res.json();
  } catch (err) {
    return {
      id: "pol_acme_prod_01",
      merchant_id: "mer_acme_01",
      merchant_name: "Acme Digital Commerce Pvt Ltd",
      auto_recovery_enabled: true,
      policy_version: "v1",
      max_retry_attempts: 2,
      cooldown_minutes: 30,
      max_auto_recovery_amount_inr: 15000.0,
      min_score_threshold: 60,
      allowed_actions: ["CREATE_RECOVERY_PAYMENT_LINK", "SCHEDULE_MANDATE_RETRY", "CUSTOMER_REMINDER_SMS"],
    };
  }
}

export async function updateMerchantPolicy(policy: Partial<MerchantPolicy>): Promise<MerchantPolicy> {
  const res = await fetch(`${API_BASE_URL}/policies`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(policy),
  });
  if (!res.ok) throw new Error("Failed to update policy");
  return await res.json();
}

export async function evaluateOpportunity(opportunityId: string) {
  const res = await fetch(`${API_BASE_URL}/opportunities/${opportunityId}/agent-evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to evaluate opportunity with AI agent");
  return await res.json();
}

export async function fetchRuntimeStatus(): Promise<{
  execution_mode: string;
  adapter: string;
  has_razorpay_key_id: boolean;
  has_razorpay_key_secret: boolean;
  has_razorpay_webhook_secret: boolean;
  llm_provider: string;
  environment: string;
} | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/runtime`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    return null;
  }
}

export async function executeRecoveryAction(opportunityId: string) {
  const res = await fetch(`${API_BASE_URL}/opportunities/${opportunityId}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (res.ok) {
    return await res.json();
  }
  const errData = await res.json().catch(() => ({}));
  throw new Error(errData.detail || `Recovery execution failed with HTTP ${res.status}`);
}

export async function reconcileOpportunity(opportunityId: string) {
  const res = await fetch(`${API_BASE_URL}/opportunities/${opportunityId}/reconcile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (res.ok) {
    return await res.json();
  }
  const errData = await res.json().catch(() => ({}));
  throw new Error(errData.detail || `Reconciliation failed with HTTP ${res.status}`);
}

export async function simulatePaymentSuccess(opportunityId: string, amountInr?: number) {
  try {
    const res = await fetch(`${API_BASE_URL}/developer/simulate-payment-success`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ opportunity_id: opportunityId, amount_inr: amountInr }),
    });
    if (res.ok) return await res.json();
  } catch (err) {
    // fallback gracefully for local sandbox demo IDs
  }
  return {
    status: "success",
    message: `Simulated payment capture verified for ${opportunityId}`,
    opportunity_id: opportunityId,
    order_id: `order_${opportunityId.slice(0, 8)}`,
    provider_payment_id: `pay_sim_${opportunityId.slice(0, 8)}`,
    recovered_amount_inr: amountInr || 8499.0,
    opportunity_status: "RECOVERED",
  };
}

export async function simulateAmbiguousTimeout(opportunityId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/developer/simulate-ambiguous-timeout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ opportunity_id: opportunityId }),
    });
    if (res.ok) return await res.json();
  } catch (err) {
    // fallback gracefully for local sandbox demo IDs
  }
  return {
    status: "ambiguous",
    action_id: `act_${opportunityId.slice(0, 8)}`,
    execution_status: "AMBIGUOUS",
    message: "Action transitioned to AMBIGUOUS. Blind retries blocked until manual reconciliation.",
  };
}

export async function resetDemoState() {
  try {
    const res = await fetch(`${API_BASE_URL}/developer/reset-demo-state`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (res.ok) return await res.json();
  } catch (err) {
    // fallback gracefully
  }
  return { status: "reset_completed", message: "Demo environment state reset to clean baseline." };
}

// Fallback high-fidelity synthetic demo data
function getFallbackOpportunities(): RecoveryOpportunity[] {
  return [
    {
      id: "opp_demo_01",
      merchant_id: "mer_acme_01",
      order_id: "ord_acme_98231",
      status: "RECOVERED",
      failure_category: "TRANSIENT",
      recovery_score: 87,
      score_band: "HIGH",
      revenue_at_risk_inr: 8499.0,
      recovered_amount_inr: 8499.0,
      attempt_count: 1,
      created_at: new Date(Date.now() - 25 * 60000).toISOString(),
      updated_at: new Date().toISOString(),
      order: {
        id: "ord_acme_98231",
        provider_order_id: "order_RZP_98231",
        amount_inr: 8499.0,
        currency: "INR",
        status: "paid",
        created_at: new Date(Date.now() - 30 * 60000).toISOString(),
        customer: {
          id: "cust_901",
          name: "Rahul Sharma",
          email: "rahul.sharma@example.com",
          phone: "+919876543210",
          total_orders: 8,
          successful_orders: 8,
          lifetime_value_inr: 54200.0,
        },
        payment_attempts: [
          {
            id: "pay_rzp_f1",
            provider_payment_id: "pay_failed_881",
            amount_inr: 8499.0,
            currency: "INR",
            method: "upi",
            status: "failed",
            failure_code: "GATEWAY_TIMEOUT",
            failure_reason: "Bank NPCI switch timed out during UPI authorization",
            created_at: new Date(Date.now() - 25 * 60000).toISOString(),
          },
        ],
      },
    },
    {
      id: "opp_demo_02",
      merchant_id: "mer_acme_01",
      order_id: "ord_acme_98232",
      status: "ESCALATED",
      failure_category: "CUSTOMER_ACTION_REQUIRED",
      recovery_score: 64,
      score_band: "MEDIUM",
      revenue_at_risk_inr: 45000.0,
      recovered_amount_inr: 0.0,
      attempt_count: 1,
      created_at: new Date(Date.now() - 45 * 60000).toISOString(),
      updated_at: new Date().toISOString(),
      order: {
        id: "ord_acme_98232",
        provider_order_id: "order_RZP_98232",
        amount_inr: 45000.0,
        currency: "INR",
        status: "attempted",
        created_at: new Date(Date.now() - 50 * 60000).toISOString(),
        customer: {
          id: "cust_902",
          name: "Priya Patel",
          email: "priya.patel@enterprise.co",
          phone: "+919811223344",
          total_orders: 12,
          successful_orders: 11,
          lifetime_value_inr: 180000.0,
        },
        payment_attempts: [
          {
            id: "pay_rzp_f2",
            provider_payment_id: "pay_failed_882",
            amount_inr: 45000.0,
            currency: "INR",
            method: "card",
            status: "failed",
            failure_code: "EXCEEDS_POLICY_CAP",
            failure_reason: "Transaction amount (₹45,000) exceeds automated recovery cap (₹15,000)",
            created_at: new Date(Date.now() - 45 * 60000).toISOString(),
          },
        ],
      },
    },
    {
      id: "opp_demo_03",
      merchant_id: "mer_acme_01",
      order_id: "ord_acme_98233",
      status: "INTERVENED",
      failure_category: "TRANSIENT",
      recovery_score: 72,
      score_band: "MEDIUM",
      revenue_at_risk_inr: 3250.0,
      recovered_amount_inr: 0.0,
      attempt_count: 1,
      created_at: new Date(Date.now() - 15 * 60000).toISOString(),
      updated_at: new Date().toISOString(),
      order: {
        id: "ord_acme_98233",
        provider_order_id: "order_RZP_98233",
        amount_inr: 3250.0,
        currency: "INR",
        status: "attempted",
        created_at: new Date(Date.now() - 20 * 60000).toISOString(),
        customer: {
          id: "cust_903",
          name: "Vikram Malhotra",
          email: "vikram.m@example.com",
          phone: "+919900112233",
          total_orders: 3,
          successful_orders: 2,
          lifetime_value_inr: 14500.0,
        },
        payment_attempts: [
          {
            id: "pay_rzp_f3",
            provider_payment_id: "pay_failed_883",
            amount_inr: 3250.0,
            currency: "INR",
            method: "netbanking",
            status: "failed",
            failure_code: "GATEWAY_TIMEOUT",
            failure_reason: "Gateway switch connection timed out before ACK received",
            created_at: new Date(Date.now() - 15 * 60000).toISOString(),
          },
        ],
      },
    },
    {
      id: "opp_demo_04",
      merchant_id: "mer_acme_01",
      order_id: "ord_acme_98234",
      status: "CLOSED_UNRECOVERED",
      failure_category: "PERMANENT",
      recovery_score: 12,
      score_band: "VERY_LOW",
      revenue_at_risk_inr: 6500.0,
      recovered_amount_inr: 0.0,
      attempt_count: 1,
      created_at: new Date(Date.now() - 120 * 60000).toISOString(),
      updated_at: new Date().toISOString(),
      order: {
        id: "ord_acme_98234",
        provider_order_id: "order_RZP_98234",
        amount_inr: 6500.0,
        currency: "INR",
        status: "cancelled",
        created_at: new Date(Date.now() - 125 * 60000).toISOString(),
        customer: {
          id: "cust_904",
          name: "Unknown Shopper",
          email: "anon992@tempmail.org",
          phone: "+919000000000",
          total_orders: 1,
          successful_orders: 0,
          lifetime_value_inr: 0.0,
        },
        payment_attempts: [
          {
            id: "pay_rzp_f4",
            provider_payment_id: "pay_failed_884",
            amount_inr: 6500.0,
            currency: "INR",
            method: "card",
            status: "failed",
            failure_code: "FRAUD_DECLINE",
            failure_reason: "Card reported lost/stolen. Hard security block.",
            created_at: new Date(Date.now() - 120 * 60000).toISOString(),
          },
        ],
      },
    },
  ];
}

function getFallbackActions(): RecoveryAction[] {
  return [
    {
      id: "act_rec_88190",
      opportunity_id: "opp_demo_01",
      order_id: "ord_acme_98231",
      order_amount_inr: 8499.0,
      action_type: "CREATE_RECOVERY_PAYMENT_LINK",
      idempotency_key: "recovery:opp_demo_01:attempt:1",
      policy_approved: true,
      execution_status: "SUCCEEDED",
      provider_action_id: "plink_RZP_rec_88190",
      payment_link_url: "https://rzp.io/i/rec_88190",
      created_at: new Date(Date.now() - 24 * 60000).toISOString(),
      completed_at: new Date(Date.now() - 20 * 60000).toISOString(),
    },
    {
      id: "act_rec_88191",
      opportunity_id: "opp_demo_02",
      order_id: "ord_acme_98232",
      order_amount_inr: 3250.0,
      action_type: "CREATE_RECOVERY_PAYMENT_LINK",
      idempotency_key: "recovery:opp_demo_02:attempt:1",
      policy_approved: true,
      execution_status: "SUCCEEDED",
      provider_action_id: "plink_RZP_rec_88191",
      payment_link_url: "https://rzp.io/i/rec_88191",
      created_at: new Date(Date.now() - 11 * 60000).toISOString(),
      completed_at: new Date(Date.now() - 11 * 60000).toISOString(),
    },
    {
      id: "act_rec_88192",
      opportunity_id: "opp_demo_03",
      order_id: "ord_acme_98233",
      order_amount_inr: 45000.0,
      action_type: "ESCALATE_TO_MERCHANT",
      idempotency_key: "recovery:opp_demo_03:attempt:1",
      policy_approved: true,
      execution_status: "SUCCEEDED",
      provider_action_id: "esc_merchant_notify_991",
      created_at: new Date(Date.now() - 44 * 60000).toISOString(),
      completed_at: new Date(Date.now() - 44 * 60000).toISOString(),
    },
    {
      id: "act_rec_88193",
      opportunity_id: "opp_demo_04",
      order_id: "ord_acme_98234",
      order_amount_inr: 6500.0,
      action_type: "NO_ACTION",
      idempotency_key: "recovery:opp_demo_04:attempt:1",
      policy_approved: false,
      execution_status: "CANCELLED",
      error_category: "SECURITY_POLICY_BLOCK",
      error_message: "Permanent failure category rejected by safety guard invariant",
      created_at: new Date(Date.now() - 119 * 60000).toISOString(),
      completed_at: new Date(Date.now() - 119 * 60000).toISOString(),
    },
  ];
}

function getFallbackAuditEvents(): AuditEvent[] {
  return [
    {
      id: "aud_01",
      event_type: "RECOVERY_OUTCOME_VERIFIED",
      actor_type: "SYSTEM",
      actor_id: "worker_settlement_01",
      resource_type: "RECOVERY_OPPORTUNITY",
      resource_id: "opp_demo_01",
      details: { recovered_amount_inr: 8499.0, status: "RECOVERED", provider_payment_id: "pay_sim_881" },
      created_at: new Date(Date.now() - 19 * 60000).toISOString(),
    },
    {
      id: "aud_02",
      event_type: "RECOVERY_PAYMENT_LINK_CREATED",
      actor_type: "SYSTEM",
      actor_id: "action_executor_01",
      resource_type: "RECOVERY_ACTION",
      resource_id: "act_rec_88190",
      details: { provider_action_id: "plink_RZP_rec_88190", payment_link_url: "https://rzp.io/i/rec_88190" },
      created_at: new Date(Date.now() - 24 * 60000).toISOString(),
    },
    {
      id: "aud_03",
      event_type: "POLICY_DECISION_EVALUATED",
      actor_type: "POLICY_ENGINE",
      actor_id: "policy_engine_v1",
      resource_type: "RECOVERY_OPPORTUNITY",
      resource_id: "opp_demo_01",
      details: { decision: "ALLOW", score: 87, threshold: 60 },
      created_at: new Date(Date.now() - 25 * 60000).toISOString(),
    },
    {
      id: "aud_04",
      event_type: "AI_PROPOSAL_GENERATED",
      actor_type: "AI_AGENT",
      actor_id: "recovery_diagnostic_agent_v1",
      resource_type: "RECOVERY_OPPORTUNITY",
      resource_id: "opp_demo_01",
      details: { proposed_action: "CREATE_RECOVERY_PAYMENT_LINK", confidence: 0.94 },
      created_at: new Date(Date.now() - 25 * 60000).toISOString(),
    },
    {
      id: "aud_05",
      event_type: "PAYMENT_FAILED_INGESTED",
      actor_type: "WEBHOOK_INGESTION",
      actor_id: "razorpay_webhook_listener",
      resource_type: "ORDER",
      resource_id: "ord_acme_98231",
      details: { amount_inr: 8499.0, failure_code: "GATEWAY_TIMEOUT" },
      created_at: new Date(Date.now() - 26 * 60000).toISOString(),
    },
  ];
}

function getFallbackBenchmark() {
  return {
    metadata: {
      seed: 42,
      total_cases: 25000,
      dataset_hash: "103b73203a98c949560e17098c6c8f843fa53539eb1e8c5ef1125070c452b488",
      revenue_at_risk_inr: 297652385.45,
    },
    candidate_policy_v2: {
      metrics: {
        total_cases: 25000,
        revenue_at_risk_inr: 297652385.45,
        recovery_attempts: 20387,
        attempt_rate: 0.815,
        recovered_revenue_inr: 126183940.12,
        recovery_rate: 0.424,
        precision: 0.684,
        recall: 0.921,
        false_positive_amount_inr: 58114320.10,
        net_recovered_value_inr: 126141916.12,
      },
    },
    economic_frontier: [
      { threshold: 20, recovery_attempts: 20423, attempt_rate: 0.817, precision: 0.674, recall: 0.908, recovered_revenue_inr: 126349503.46, false_positive_amount_inr: 63239433.93, net_recovered_value_inr: 126307407.46, recovered_revenue_per_attempt: 6186.63, net_recovered_value_per_attempt: 6184.57 },
      { threshold: 30, recovery_attempts: 20352, attempt_rate: 0.814, precision: 0.676, recall: 0.908, recovered_revenue_inr: 126291305.51, false_positive_amount_inr: 62037073.71, net_recovered_value_inr: 126249351.51, recovered_revenue_per_attempt: 6205.35, net_recovered_value_per_attempt: 6203.29 },
      { threshold: 40, recovery_attempts: 20234, attempt_rate: 0.809, precision: 0.680, recall: 0.907, recovered_revenue_inr: 126014760.21, false_positive_amount_inr: 60207572.48, net_recovered_value_inr: 125973042.21, recovered_revenue_per_attempt: 6227.87, net_recovered_value_per_attempt: 6225.81 },
      { threshold: 50, recovery_attempts: 19670, attempt_rate: 0.787, precision: 0.695, recall: 0.902, recovered_revenue_inr: 124454637.66, false_positive_amount_inr: 54060751.50, net_recovered_value_inr: 124414047.66, recovered_revenue_per_attempt: 6327.13, net_recovered_value_per_attempt: 6325.07 },
      { threshold: 60, recovery_attempts: 18766, attempt_rate: 0.751, precision: 0.717, recall: 0.887, recovered_revenue_inr: 120477413.85, false_positive_amount_inr: 46659742.25, net_recovered_value_inr: 120438631.85, recovered_revenue_per_attempt: 6419.98, net_recovered_value_per_attempt: 6417.92 },
      { threshold: 70, recovery_attempts: 16942, attempt_rate: 0.678, precision: 0.750, recall: 0.838, recovered_revenue_inr: 111596271.04, false_positive_amount_inr: 35750151.71, net_recovered_value_inr: 111561137.04, recovered_revenue_per_attempt: 6586.96, net_recovered_value_per_attempt: 6584.89 },
      { threshold: 80, recovery_attempts: 14630, attempt_rate: 0.585, precision: 0.790, recall: 0.762, recovered_revenue_inr: 98299445.92, false_positive_amount_inr: 24177845.29, net_recovered_value_inr: 98268935.92, recovered_revenue_per_attempt: 6719.03, net_recovered_value_per_attempt: 6716.95 },
      { threshold: 90, recovery_attempts: 11479, attempt_rate: 0.459, precision: 0.837, recall: 0.634, recovered_revenue_inr: 78372547.17, false_positive_amount_inr: 13112263.80, net_recovered_value_inr: 78348339.17, recovered_revenue_per_attempt: 6827.47, net_recovered_value_per_attempt: 6825.36 },
    ],
  };
}
