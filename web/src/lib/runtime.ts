export type TraceStep = {
  type: string;
  token?: string;
  value?: string;
  event_class?: string;
  from_state?: string;
  action?: string;
  to_state?: string;
  output?: string | null;
  literal?: boolean;
  cursor?: number;
  message?: string;
  error_type?: string;
  state?: string;
};

export type RuntimeError = {
  token?: string;
  event_class?: string;
  message: string;
  type?: string;
};

export type RuntimeResult = {
  status: "ok" | "error";
  state: string;
  buffer: string[];
  mode: string | null;
  outputs: string[];
  trace: TraceStep[];
  error: RuntimeError | null;
  cursor: number;
  session_id?: string;
  source: "api" | "mock";
  sourceLabel: string;
  apiBaseUrl?: string;
};

export type RuntimeRequest = {
  tokens: string[];
};

export type Example = {
  label: string;
  tokens: string;
  description: string;
};

export const examples: Example[] = [
  {
    label: "Basic implication",
    tokens: "C C . 3 3 SPACE",
    description: "Commit emits CC->33.",
  },
  {
    label: "Escape literal",
    tokens: "A _ . B",
    description: "The escape marker makes the next token literal.",
  },
  {
    label: "Reduce direct",
    tokens: "A . B",
    description: "Runtime auto-commit emits A->B.",
  },
  {
    label: "Invalid token",
    tokens: "INVALID_TOKEN",
    description: "Shows clean validation failure handling.",
  },
];

export function parseTokens(input: string): string[] {
  return input.trim().split(/\s+/).filter(Boolean);
}

function transition(
  cursor: number,
  token: string,
  eventClass: string,
  fromState: string,
  action: string,
  toState: string,
  output: string | null = null,
  literal = false,
): TraceStep {
  return {
    type: "transition",
    cursor,
    token,
    event_class: eventClass,
    from_state: fromState,
    action,
    to_state: toState,
    output,
    literal,
    value: token,
  };
}

const knownMockResults: Record<string, Omit<RuntimeResult, "source" | "sourceLabel">> = {
  "C C . 3 3 SPACE": {
    status: "ok",
    state: "IDLE",
    buffer: [],
    mode: null,
    outputs: ["CC→33"],
    cursor: 6,
    session_id: "mock-basic",
    error: null,
    trace: [
      transition(0, "C", "CONTENT", "IDLE", "append", "COMPOSE"),
      transition(1, "C", "CONTENT", "COMPOSE", "append", "COMPOSE"),
      transition(2, ".", "BIND", "COMPOSE", "mark_bind", "COMPOSE"),
      transition(3, "3", "CONTENT", "COMPOSE", "append", "COMPOSE"),
      transition(4, "3", "CONTENT", "COMPOSE", "append", "COMPOSE"),
      transition(5, "SPACE", "COMMIT", "COMPOSE", "reduce_and_emit", "IDLE", "CC→33"),
    ],
  },
  "A _ . B": {
    status: "ok",
    state: "IDLE",
    buffer: [],
    mode: null,
    outputs: ["A.B"],
    cursor: 4,
    session_id: "mock-escape",
    error: null,
    trace: [
      transition(0, "A", "CONTENT", "IDLE", "append", "COMPOSE"),
      {
        type: "escape",
        cursor: 1,
        value: "_",
        event_class: "ESCAPE",
        from_state: "COMPOSE",
        action: "escape_next",
        to_state: "COMPOSE",
        output: null,
        literal: false,
      },
      transition(1, ".", "CONTENT", "COMPOSE", "append", "COMPOSE", null, true),
      transition(2, "B", "CONTENT", "COMPOSE", "append", "COMPOSE"),
      transition(3, "SPACE", "COMMIT", "COMPOSE", "reduce_and_emit", "IDLE", "A.B"),
    ],
  },
  "A . B": {
    status: "ok",
    state: "IDLE",
    buffer: [],
    mode: null,
    outputs: ["A→B"],
    cursor: 4,
    session_id: "mock-reduce",
    error: null,
    trace: [
      transition(0, "A", "CONTENT", "IDLE", "append", "COMPOSE"),
      transition(1, ".", "BIND", "COMPOSE", "mark_bind", "COMPOSE"),
      transition(2, "B", "CONTENT", "COMPOSE", "append", "COMPOSE"),
      transition(3, "SPACE", "COMMIT", "COMPOSE", "reduce_and_emit", "IDLE", "A→B"),
    ],
  },
  INVALID_TOKEN: {
    status: "error",
    state: "ERROR",
    buffer: [],
    mode: null,
    outputs: [],
    cursor: 0,
    session_id: "mock-invalid",
    error: {
      token: "INVALID_TOKEN",
      event_class: "INVALID",
      message: "Token has no GDk9 jurisdiction or no valid transition",
      type: "TokenValidationError",
    },
    trace: [
      {
        type: "error",
        cursor: 0,
        token: "INVALID_TOKEN",
        state: "ERROR",
        message: "Token has no GDk9 jurisdiction or no valid transition",
        error_type: "TokenValidationError",
      },
    ],
  },
};

export function mockRuntime(tokens: string[]): RuntimeResult {
  const key = tokens.join(" ");
  const result = knownMockResults[key];

  if (result) {
    return {
      ...result,
      source: "mock",
      sourceLabel: "Demo mode: known sample response",
    };
  }

  return {
    status: "error",
    state: "DEMO_ONLY",
    buffer: [],
    mode: null,
    outputs: [],
    cursor: 0,
    session_id: "mock-demo-only",
    source: "mock",
    sourceLabel: "Demo mode: connect the API for custom streams",
    error: {
      message:
        "The local mock only returns vetted sample outputs. Start the Python API server to run arbitrary token streams.",
      type: "DemoModeUnavailable",
    },
    trace: [],
  };
}

export function normalizeRuntimePayload(payload: Partial<RuntimeResult>, apiBaseUrl?: string): RuntimeResult {
  return {
    status: payload.status === "error" ? "error" : "ok",
    state: payload.state ?? "UNKNOWN",
    buffer: Array.isArray(payload.buffer) ? payload.buffer : [],
    mode: payload.mode ?? null,
    outputs: Array.isArray(payload.outputs) ? payload.outputs : [],
    trace: Array.isArray(payload.trace) ? payload.trace : [],
    error: payload.error ?? null,
    cursor: typeof payload.cursor === "number" ? payload.cursor : 0,
    session_id: payload.session_id,
    source: "api",
    sourceLabel: "Live API response",
    apiBaseUrl,
  };
}
