export interface SourceItem {
  episode: string;
  guest: string;
  timestamp?: string;
  text?: string;
  score: number;
}

export interface ArtifactItem {
  id?: string;
  identifier: string;
  title: string;
  artifact_type: 'markdown' | 'html';
  content: string;
  created_at?: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceItem[];
  artifacts?: ArtifactItem[];
  created_at: string;
  isStreaming?: boolean;
}

export interface Session {
  id: string;
  title: string;
  provider: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface SessionListItem {
  id: string;
  title: string;
  provider: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}


export interface HealthStatus {
  status: string;
  database: string;
  pgvector: string;
  chunks_indexed: number;
  providers: {
    ollama?: {
      available: boolean;
      endpoint: string;
      target_model: string;
      installed_models: string[];
    };
    cloud?: {
      configured: boolean;
    };
  };
}
