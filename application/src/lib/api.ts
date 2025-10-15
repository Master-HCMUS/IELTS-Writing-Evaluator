// API client for communicating with the FastAPI backend

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface GenerateQuestionRequest {
  difficulty?: 'easy' | 'medium' | 'hard';
  topic?: string;
}

export interface GenerateQuestionResponse {
  id: string;
  question: string;
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  run_id: string;
  generated_at: string;
}

export interface ScoreRequest {
  task_type: 'task2';
  essay: string;
  question?: string;
  options?: {
    max_evidence?: number;
  };
}

export interface ScoreResponse {
  per_criterion: Array<{
    name: string;
    band: number;
    evidence_quotes: string[];
    errors: Array<{
      span: string;
      type: 'grammar' | 'lexical' | 'coherence' | 'task' | 'other';
      fix: string;
    }>;
    suggestions: string[];
  }>;
  overall: number;
  votes: number[];
  dispersion: number;
  confidence: 'high' | 'low';
  meta: {
    prompt_hash: string;
    model: string;
    schema_version: string;
    rubric_version: string;
    token_usage: {
      input_tokens: number;
      output_tokens: number;
    };
  };
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  async generateQuestion(request: GenerateQuestionRequest = {}): Promise<GenerateQuestionResponse> {
    return this.request<GenerateQuestionResponse>('/generate-question', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async scoreEssay(request: ScoreRequest): Promise<ScoreResponse> {
    return this.request<ScoreResponse>('/score', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async healthCheck(): Promise<{ status: string; env: string }> {
    return this.request('/healthz');
  }
}

export const apiClient = new ApiClient();