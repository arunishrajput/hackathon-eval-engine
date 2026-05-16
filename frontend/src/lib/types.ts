export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: 'admin' | 'participant';
  is_active: boolean;
  created_at: string;
}

export interface Criterion {
  id: string;
  name: string;
  description?: string;
  weight: number;
  agent_id?: string;
  display_order: number;
}

export interface Hackathon {
  id: string;
  title: string;
  description?: string;
  admin_id: string;
  status: 'draft' | 'active' | 'evaluating' | 'finalized';
  start_date?: string;
  end_date?: string;
  max_submissions: number;
  settings: Record<string, unknown>;
  created_at: string;
  criteria: Criterion[];
}

export interface Submission {
  id: string;
  hackathon_id: string;
  user_id: string;
  repo_url: string;
  repo_name?: string;
  repo_description?: string;
  status: 'pending' | 'cloning' | 'analyzing' | 'evaluating' | 'completed' | 'failed';
  error_message?: string;
  submitted_at: string;
  clone_completed_at?: string;
  analysis_completed_at?: string;
  evaluation_completed_at?: string;
}

export interface EvidenceItem {
  finding: string;
  impact: 'high' | 'medium' | 'low';
  file_ref?: string;
}

export interface AgentResult {
  id: string;
  agent_id: string;
  criterion_id?: string;
  score_raw?: number;
  confidence?: number;
  evidence: string[];
  evidence_items?: EvidenceItem[];
  strengths: string[];
  weaknesses: string[];
  reasoning?: string;
  abstained: boolean;
  abstain_reason?: string;
  processing_time_ms?: number;
  created_at: string;
}

export interface EvaluationReport {
  generated_at: string;
  final_score: number;
  grade: string;
  summary?: string;
  top_strengths: string[];
  top_weaknesses: string[];
  recommendations?: string[];
  metadata: {
    total_files: number;
    total_lines: number;
    languages: string[];
    has_tests: boolean;
    has_docker: boolean;
    has_ci?: boolean;
    primary_language?: string;
  };
}

export interface Evaluation {
  id: string;
  submission_id: string;
  hackathon_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  final_score?: number;
  report?: EvaluationReport;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  agent_results: AgentResult[];
}

export interface Ranking {
  id: string;
  hackathon_id: string;
  submission_id: string;
  rank: number;
  final_score: number;
  normalized_score?: number;
  percentile?: number;
  finalized: boolean;
  created_at: string;
}

export interface LeaderboardEntry {
  rank: number;
  submission_id: string;
  user_full_name?: string;
  repo_name?: string;
  repo_url?: string;
  final_score?: number;
  normalized_score?: number;
  percentile?: number;
}

export interface LeaderboardResponse {
  hackathon_id: string;
  total_submissions: number;
  finalized: boolean;
  entries: LeaderboardEntry[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  retrieved_chunks: unknown[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  submission_id: string;
  hackathon_id: string;
  created_at: string;
  last_message_at?: string;
  messages: ChatMessage[];
}

export type EvaluationStage =
  | 'pending'
  | 'cloning'
  | 'analyzing'
  | 'evaluating'
  | 'completed'
  | 'failed';

export interface StreamEvent {
  status: EvaluationStage;
  message?: string;
  progress?: number;
  agent_count?: number;
}
