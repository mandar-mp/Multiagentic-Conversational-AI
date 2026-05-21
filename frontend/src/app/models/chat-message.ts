export interface TraceSummary {
  intent?: string;
  intent_confidence?: number;
  routing_decision?: string;
  selected_capability?: string;
  answer_source?: string;
  duration_ms?: number;
}

export interface TraceAgent {
  name: string;
  role: string;
  status: string;
  detail?: string;
}

export interface CapabilityMatch {
  capability_name?: string;
  confidence?: number;
  reason?: string;
}

export interface TracePlanStep {
  step_id?: string;
  agent_name?: string;
  action?: string;
  requires_approval?: boolean;
  status?: string;
}

export interface TraceExecutionResult {
  agent_name?: string;
  status?: string;
  message?: string;
  error?: string;
}

export interface ChatTrace {
  summary?: TraceSummary;
  agents?: TraceAgent[];
  capability_matches?: CapabilityMatch[];
  plan?: TracePlanStep[];
  authorization?: Record<string, any>;
  guardrails?: Record<string, any>;
  execution_results?: TraceExecutionResult[];
  conversation_context?: Record<string, any>;
  model?: {
    provider?: string;
    name?: string;
  };
  audit_logged?: boolean;
  workflow_fallback?: boolean;
}

export interface ChatMetadata {
  provider?: string;
  model?: string;
  intent?: string;
  intent_confidence?: number;
  routing_decision?: string;
  capability_matches?: CapabilityMatch[];
  plan?: TracePlanStep[];
  authorization?: Record<string, any>;
  guardrails?: Record<string, any>;
  execution_results?: TraceExecutionResult[];
  audit_logged?: boolean;
  duration_ms?: number;
  workflow_fallback?: boolean;
  trace?: ChatTrace;
  [key: string]: any;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: ChatMetadata;
}
